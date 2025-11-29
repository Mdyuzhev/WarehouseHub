"""
Warehouse Telegram Bot v5.0
Главная точка входа - теперь чистая и красивая! 🎯

Архитектура:
- config.py - конфигурация
- services/ - интеграции (GitLab, Locust, Allure, Health)
- bot/ - логика бота
  - telegram.py - низкоуровневая работа с Telegram API
  - keyboards.py - клавиатуры
  - messages.py - форматирование + юмор
  - handlers/ - обработчики команд
"""

import asyncio
import signal
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

# Наши модули
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GITLAB_WEBHOOK_SECRET, GITLAB_JOBS,
    LOG_FORMAT, LOG_LEVEL
)
from bot.telegram import get_updates, send_message_with_reply_keyboard, answer_callback_query
from bot.keyboards import get_reply_keyboard, get_main_menu_keyboard
from bot.handlers import (
    # Commands
    handle_start, handle_help, handle_menu, handle_health, handle_joke,
    handle_metrics, handle_pods,
    # Deploy
    handle_deploy_menu, request_deploy_password, handle_deploy_password_input,
    is_pending_deploy_password,
    # Testing
    handle_e2e_run, handle_e2e_report, handle_load_menu, handle_load_target,
    handle_load_users, handle_load_duration, request_password,
    handle_password_input, handle_stop_load_test, handle_load_status,
    is_pending_password, is_pending_wizard,
    # Claude
    handle_claude_menu, handle_claude_input, is_pending_claude,
    # GitLab Webhooks
    handle_gitlab_webhook,
)

# =============================================================================
# Настройка логирования
# =============================================================================
def setup_logging():
    """Настройка логирования с поддержкой JSON формата для K8s."""
    import json
    import sys

    class JsonFormatter(logging.Formatter):
        """JSON formatter для структурированного логирования."""
        def format(self, record):
            log_obj = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "service": "telegram-bot",
                "version": "5.0.0"
            }
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)
            if hasattr(record, "chat_id"):
                log_obj["chat_id"] = record.chat_id
            if hasattr(record, "command"):
                log_obj["command"] = record.command
            if hasattr(record, "user_id"):
                log_obj["user_id"] = record.user_id
            return json.dumps(log_obj, ensure_ascii=False)

    # Уровень логирования
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    # Формат: JSON для K8s, текстовый для локальной разработки
    if LOG_FORMAT.lower() == "json":
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logging.root.handlers = [handler]
        logging.root.setLevel(level)
    else:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Уменьшаем шум от httpx и других библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger(__name__)

# Последний обработанный update_id
last_update_id = 0

# Флаг для graceful shutdown
shutdown_event = asyncio.Event()
polling_task = None


# =============================================================================
# FastAPI App
# =============================================================================

def handle_shutdown(signum, frame):
    """Обработчик сигналов SIGTERM/SIGINT для graceful shutdown."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager с graceful shutdown."""
    global polling_task

    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    logger.info("Bot started with polling")
    # Запускаем polling в фоне
    polling_task = asyncio.create_task(telegram_polling())
    logger.info("Starting Telegram polling... 🤖")

    yield

    # Graceful shutdown
    logger.info("Initiating graceful shutdown...")
    shutdown_event.set()

    # Ждём завершения polling task
    if polling_task:
        try:
            await asyncio.wait_for(polling_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Polling task did not stop in time, cancelling...")
            polling_task.cancel()

    logger.info("Bot stopped gracefully")


app = FastAPI(
    title="Warehouse Telegram Bot",
    description="CI/CD notifications and orchestration",
    version="5.0.0",
    lifespan=lifespan
)


# =============================================================================
# Telegram Polling
# =============================================================================

async def telegram_polling():
    """Основной цикл polling с graceful shutdown и retry backoff."""
    global last_update_id
    consecutive_errors = 0
    max_backoff = 60  # Максимальная задержка при ошибках

    while not shutdown_event.is_set():
        try:
            updates = await get_updates(offset=last_update_id + 1)

            # Сброс счётчика ошибок при успехе
            if updates is not None:
                consecutive_errors = 0

            for update in updates:
                if shutdown_event.is_set():
                    break

                last_update_id = update.get("update_id", last_update_id)

                # Callback query (inline кнопки)
                if "callback_query" in update:
                    await process_callback(update["callback_query"])

                # Обычное сообщение
                elif "message" in update:
                    message = update["message"]
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")

                    if chat_id and text:
                        await process_command(chat_id, text)

        except asyncio.CancelledError:
            logger.info("Polling cancelled, exiting...")
            break
        except Exception as e:
            consecutive_errors += 1
            # Экспоненциальный backoff: 5, 10, 20, 40, 60 секунд
            backoff = min(5 * (2 ** (consecutive_errors - 1)), max_backoff)
            logger.error(f"Polling error (attempt {consecutive_errors}): {e}")
            logger.info(f"Retrying in {backoff} seconds...")

            # Ждём с возможностью прерывания при shutdown
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=backoff)
                break  # shutdown_event установлен
            except asyncio.TimeoutError:
                pass  # Таймаут истёк, продолжаем polling

    logger.info("Polling loop stopped")


async def process_command(chat_id: int, text: str):
    """Главный роутер команд."""
    # Логируем входящую команду (без паролей!)
    log_text = "[HIDDEN]" if is_pending_password(chat_id) or is_pending_deploy_password(chat_id) else text
    logger.info(f"Command received: chat_id={chat_id}, text='{log_text}'")

    # Проверяем ожидание ввода
    if is_pending_deploy_password(chat_id):
        await handle_deploy_password_input(chat_id, text)
        return

    if is_pending_password(chat_id):
        await handle_password_input(chat_id, text)
        return

    if is_pending_claude(chat_id):
        await handle_claude_input(chat_id, text)
        return

    # Reply keyboard кнопки
    if text == "🏥 Статус":
        await handle_health(chat_id)
    elif text == "📊 Метрики":
        await handle_metrics(chat_id)
    elif text == "🚀 Деплой":
        await handle_deploy_menu(chat_id)
    elif text == "🧪 E2E":
        await handle_e2e_run(chat_id)
    elif text == "🔥 Нагрузка":
        await handle_load_menu(chat_id)
    elif text == "🛑 Стоп":
        await handle_stop_load_test(chat_id)
    elif text == "🤖 Claude":
        await handle_claude_menu(chat_id)
    elif text == "🎰 Шутка":
        await handle_joke(chat_id)
    elif text == "❓":
        await handle_help(chat_id)

    # Slash команды
    elif text == "/start":
        await handle_start(chat_id)
    elif text in ["/help", "/?"]:
        await handle_help(chat_id)
    elif text == "/menu":
        await handle_menu(chat_id)
    elif text in ["/health", "/status"]:
        await handle_health(chat_id)
    elif text == "/pods":
        await handle_pods(chat_id)
    elif text == "/joke":
        await handle_joke(chat_id)

    # Deploy команды (требуют пароль)
    elif text == "/deploy":
        await handle_deploy_menu(chat_id)
    elif text == "/deploy_api_staging":
        await request_deploy_password(chat_id, "deploy_api_staging", "API", "staging")
    elif text == "/deploy_frontend_staging":
        await request_deploy_password(chat_id, "deploy_frontend_staging", "Frontend", "staging")
    elif text == "/deploy_all_staging":
        await request_deploy_password(chat_id, "deploy_all_staging", "API + Frontend", "staging")
    elif text == "/deploy_api_prod":
        await request_deploy_password(chat_id, "deploy_api_prod", "API", "prod")
    elif text == "/deploy_frontend_prod":
        await request_deploy_password(chat_id, "deploy_frontend_prod", "Frontend", "prod")
    elif text == "/deploy_all_prod":
        await request_deploy_password(chat_id, "deploy_all_prod", "API + Frontend", "prod")

    # Test команды
    elif text == "/e2e":
        await handle_e2e_run(chat_id)
    elif text == "/load":
        await handle_load_menu(chat_id)
    elif text == "/stop":
        await handle_stop_load_test(chat_id)


async def process_callback(callback_query: dict):
    """Обработчик inline кнопок."""
    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")

    if not chat_id:
        return

    # Убираем "часики"
    await answer_callback_query(callback_id)

    # Роутинг по callback_data
    if data == "health":
        await handle_health(chat_id)
    elif data == "metrics":
        await handle_metrics(chat_id)
    elif data == "menu":
        await handle_menu(chat_id)
    elif data == "help":
        await handle_help(chat_id)
    elif data == "joke":
        await handle_joke(chat_id)

    # Deploy (требуют пароль)
    elif data == "deploy_menu":
        await handle_deploy_menu(chat_id)
    elif data == "deploy_api_staging":
        await request_deploy_password(chat_id, "deploy_api_staging", "API", "staging")
    elif data == "deploy_frontend_staging":
        await request_deploy_password(chat_id, "deploy_frontend_staging", "Frontend", "staging")
    elif data == "deploy_all_staging":
        await request_deploy_password(chat_id, "deploy_all_staging", "API + Frontend", "staging")
    elif data == "deploy_api_prod":
        await request_deploy_password(chat_id, "deploy_api_prod", "API", "prod")
    elif data == "deploy_frontend_prod":
        await request_deploy_password(chat_id, "deploy_frontend_prod", "Frontend", "prod")
    elif data == "deploy_all_prod":
        await request_deploy_password(chat_id, "deploy_all_prod", "API + Frontend", "prod")

    # E2E
    elif data == "e2e_run":
        await handle_e2e_run(chat_id)
    elif data == "e2e_report":
        await handle_e2e_report(chat_id)

    # Load testing
    elif data == "load_staging":
        await handle_load_target(chat_id, "staging")
    elif data == "load_prod":
        await handle_load_target(chat_id, "prod")
    elif data == "load_stop":
        await handle_stop_load_test(chat_id)
    elif data == "load_status":
        await handle_load_status(chat_id)

    # Load test wizard
    elif data.startswith("lt_users_"):
        parts = data.split("_")
        if len(parts) == 4:
            target = parts[2]
            users_str = parts[3]
            if users_str != "custom":
                await handle_load_users(chat_id, target, int(users_str))

    elif data.startswith("lt_dur_"):
        parts = data.split("_")
        if len(parts) == 5:
            target = parts[2]
            users = int(parts[3])
            duration_str = parts[4]
            if duration_str != "custom":
                await handle_load_duration(chat_id, target, users, int(duration_str))

    elif data.startswith("lt_ramp_"):
        parts = data.split("_")
        if len(parts) == 6:
            target = parts[2]
            users = int(parts[3])
            duration = int(parts[4])
            ramp_up = parts[5]
            await request_password(chat_id, target, users, duration, ramp_up)

    elif data == "noop":
        pass  # Разделитель


# =============================================================================
# HTTP Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "5.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Warehouse Telegram Bot",
        "version": "5.0.0",
        "description": "CI/CD notifications and full orchestration control 🚀"
    }


# =============================================================================
# GitLab Webhooks (для уведомлений)
# =============================================================================

class GitLabWebhook(BaseModel):
    object_kind: Optional[str] = None
    event_name: Optional[str] = None


@app.post("/webhook/gitlab")
async def gitlab_webhook(request: Request):
    """
    Обработка GitLab webhooks для автоматических уведомлений.

    GitLab отправляет события:
    - Pipeline Hook: object_kind = "pipeline"
    - Job Hook: object_kind = "build"

    Настройка webhook в GitLab:
    1. Project → Settings → Webhooks
    2. URL: http://<bot-host>/webhook/gitlab
    3. Secret Token: (опционально, если задан GITLAB_WEBHOOK_SECRET)
    4. Triggers: Pipeline events, Job events
    """
    # Проверяем токен (если задан)
    token = request.headers.get("X-Gitlab-Token", "")
    if GITLAB_WEBHOOK_SECRET and token != GITLAB_WEBHOOK_SECRET:
        logger.warning(f"Webhook rejected: invalid token")
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        data = await request.json()
        event_type = data.get("object_kind", "unknown")

        logger.info(f"Received GitLab webhook: {event_type}")

        # Делегируем обработку handler'у
        result = await handle_gitlab_webhook(event_type, data)

        return result

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
