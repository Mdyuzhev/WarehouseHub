"""
Warehouse Telegram Bot v5.4
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
from typing import Optional, Dict, Any

# Наши модули
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GITLAB_WEBHOOK_SECRET, GITLAB_JOBS,
    LOG_FORMAT, LOG_LEVEL
)
from bot.telegram import (
    get_updates, send_message_with_reply_keyboard, answer_callback_query,
    send_message_with_inline_keyboard, edit_message_text, send_message
)
from bot.keyboards import get_reply_keyboard, get_main_menu_keyboard
from bot.messages import format_robot_notification
from bot.handlers import (
    # Commands
    handle_start, handle_help, handle_menu, handle_health, handle_joke,
    handle_metrics, handle_pods, handle_release,
    # Deploy
    handle_deploy_menu, request_deploy_password, handle_deploy_password_input,
    is_pending_deploy_password,
    # QA / Testing
    handle_qa_menu, handle_qa_env, handle_qa_test_type, handle_qa_run, handle_qa_report,
    handle_load_menu, handle_load_target,
    handle_load_users, handle_load_duration, request_password,
    handle_password_input, handle_stop_load_test, handle_load_status,
    is_pending_password,
    # Claude (код сохранён, но не используется в меню)
    handle_claude_menu, handle_claude_input, is_pending_claude,
    # PM
    handle_pm_menu, handle_in_progress, handle_stories_audit,
    handle_daily_report, handle_weekly_report, handle_issue_lookup,
    # GitLab Webhooks
    handle_gitlab_webhook,
    # Robot
    handle_robot_menu, handle_robot_status, handle_robot_stats,
    handle_robot_scenarios, handle_robot_duration_select, handle_robot_start, handle_robot_stop,
    handle_robot_speed_select, handle_robot_environment_select,
    request_robot_password, handle_robot_password_input,
    is_pending_robot_password,
    # Robot Schedule
    handle_robot_schedule_menu, handle_robot_schedule_env, handle_robot_schedule_time,
    handle_robot_schedule_create, handle_robot_scheduled_list, handle_robot_cancel_scheduled,
    request_schedule_time_input, handle_schedule_time_input, is_pending_schedule_time,
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
                "version": "5.4.0"
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
    description="CI/CD notifications, PM orchestration and robot control",
    version="5.4.0",
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
    log_text = "[HIDDEN]" if is_pending_password(chat_id) or is_pending_deploy_password(chat_id) or is_pending_robot_password(chat_id) else text
    logger.info(f"Command received: chat_id={chat_id}, text='{log_text}'")

    # Проверяем ожидание ввода
    if is_pending_deploy_password(chat_id):
        await handle_deploy_password_input(chat_id, text)
        return

    if is_pending_password(chat_id):
        await handle_password_input(chat_id, text)
        return

    if is_pending_robot_password(chat_id):
        await handle_robot_password_input(send_message_async, chat_id, text)
        return

    if is_pending_schedule_time(chat_id):
        await handle_schedule_time_input(send_message_async, chat_id, text)
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
    elif text == "🔬 QA":
        await handle_qa_menu(chat_id)
    elif text == "🛑 Стоп":
        await handle_stop_load_test(chat_id)
    elif text == "📋 PM":
        await handle_pm_menu(chat_id)
    elif text == "🤖 Claude":
        # Claude код сохранён, но скрыт из меню (WH-88)
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
    elif text == "/release":
        await handle_release(chat_id)

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
    elif text == "/qa":
        await handle_qa_menu(chat_id)
    elif text == "/e2e":
        await handle_qa_menu(chat_id)
    elif text == "/load":
        await handle_load_menu(chat_id)
    elif text == "/stop":
        await handle_stop_load_test(chat_id)

    # Robot команды
    elif text == "🤖 Robot" or text == "/robot":
        await handle_robot_menu(send_message_async, chat_id)


async def send_message_async(
    chat_id: int,
    text: str,
    parse_mode: str = "Markdown",
    reply_markup: dict = None,
    edit_message_id: int = None
):
    """
    Универсальная функция отправки сообщения для handlers.

    Args:
        chat_id: ID чата
        text: Текст сообщения
        parse_mode: Формат (Markdown или HTML)
        reply_markup: Inline keyboard
        edit_message_id: ID сообщения для редактирования
    """
    if edit_message_id:
        return await edit_message_text(
            chat_id=chat_id,
            message_id=edit_message_id,
            text=text,
            keyboard=reply_markup,
            parse_mode=parse_mode
        )
    elif reply_markup:
        return await send_message_with_inline_keyboard(
            chat_id=chat_id,
            text=text,
            keyboard=reply_markup,
            parse_mode=parse_mode
        )
    else:
        return await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )


async def process_callback(callback_query: dict):
    """Обработчик inline кнопок."""
    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")

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

    # QA Menu
    elif data == "qa_menu":
        await handle_qa_menu(chat_id)
    elif data == "qa_staging":
        await handle_qa_env(chat_id, "staging")
    elif data == "qa_prod":
        await handle_qa_env(chat_id, "prod")
    elif data.startswith("qa_e2e_") or data.startswith("qa_ui_") or data.startswith("qa_load_"):
        # qa_e2e_staging, qa_ui_prod, qa_load_staging
        parts = data.split("_")
        if len(parts) == 3:
            test_type = parts[1]  # e2e, ui, load
            env = parts[2]  # staging, prod
            await handle_qa_test_type(chat_id, test_type, env)
    elif data.startswith("qa_run_"):
        # qa_run_e2e_staging, qa_run_ui_prod
        parts = data.replace("qa_run_", "").split("_")
        if len(parts) == 2:
            test_type, env = parts
            await handle_qa_run(chat_id, test_type, env)
    elif data.startswith("qa_report_"):
        # qa_report_e2e_staging, qa_report_ui_prod
        parts = data.replace("qa_report_", "").split("_")
        if len(parts) == 2:
            test_type, env = parts
            await handle_qa_report(chat_id, test_type, env)

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

    # PM
    elif data == "pm_menu":
        await handle_pm_menu(chat_id)
    elif data == "pm_in_progress":
        await handle_in_progress(chat_id)
    elif data == "pm_audit":
        await handle_stories_audit(chat_id)
    elif data == "pm_report_day":
        await handle_daily_report(chat_id)
    elif data == "pm_report_week":
        await handle_weekly_report(chat_id)

    # Robot
    # Flow: Сценарий → Продолжительность → Окружение → Пароль → Скорость → Запуск
    elif data == "robot_menu":
        await handle_robot_menu(send_message_async, chat_id, message_id)
    elif data == "robot_status":
        await handle_robot_status(send_message_async, chat_id, message_id)
    elif data == "robot_stats":
        await handle_robot_stats(send_message_async, chat_id, message_id)
    elif data == "robot_scenarios":
        await handle_robot_scenarios(send_message_async, chat_id, message_id)
    elif data == "robot_stop":
        await handle_robot_stop(send_message_async, chat_id, message_id)
    elif data.startswith("robot_run_"):
        # robot_run_receiving, robot_run_shipping, robot_run_inventory
        # После выбора сценария показываем выбор продолжительности
        scenario = data.replace("robot_run_", "")
        await handle_robot_duration_select(send_message_async, chat_id, scenario, message_id)
    elif data.startswith("robot_dur_"):
        # robot_dur_receiving_5, robot_dur_shipping_30, etc.
        # После выбора продолжительности показываем выбор окружения
        parts = data.replace("robot_dur_", "").rsplit("_", 1)
        if len(parts) == 2:
            scenario, duration_str = parts
            duration = int(duration_str)
            await handle_robot_environment_select(send_message_async, chat_id, scenario, duration, message_id)
    elif data.startswith("robot_env_"):
        # robot_env_receiving_5_staging, robot_env_shipping_30_prod, etc.
        # После выбора окружения запрашиваем пароль
        parts = data.replace("robot_env_", "").rsplit("_", 2)
        if len(parts) == 3:
            scenario, duration_str, environment = parts
            duration = int(duration_str)
            await request_robot_password(send_message_async, chat_id, scenario, duration, environment)
    elif data.startswith("robot_speed_"):
        # robot_speed_receiving_5_staging_fast, robot_speed_shipping_30_prod_normal, etc.
        parts = data.replace("robot_speed_", "").rsplit("_", 3)
        if len(parts) == 4:
            scenario, duration_str, environment, speed = parts
            duration = int(duration_str)
            await handle_robot_start(send_message_async, chat_id, scenario, duration, speed, environment, message_id)

    # === Robot Schedule ===
    elif data == "robot_schedule":
        await handle_robot_schedule_menu(send_message_async, chat_id, message_id)
    elif data == "robot_scheduled":
        await handle_robot_scheduled_list(send_message_async, chat_id, message_id)
    elif data.startswith("robot_sched_"):
        # robot_sched_receiving, robot_sched_shipping, robot_sched_inventory
        # После выбора сценария показываем выбор окружения
        scenario = data.replace("robot_sched_", "")
        await handle_robot_schedule_env(send_message_async, chat_id, scenario, message_id)
    elif data.startswith("robot_schedenv_"):
        # robot_schedenv_receiving_staging, robot_schedenv_shipping_prod
        # После выбора окружения показываем выбор времени
        parts = data.replace("robot_schedenv_", "").rsplit("_", 1)
        if len(parts) == 2:
            scenario, environment = parts
            await handle_robot_schedule_time(send_message_async, chat_id, scenario, environment, message_id)
    elif data.startswith("robot_time_"):
        # robot_time_receiving_staging_5, robot_time_shipping_prod_custom, etc.
        parts = data.replace("robot_time_", "").rsplit("_", 2)
        if len(parts) == 3:
            scenario, environment, minutes_str = parts
            if minutes_str == "custom":
                await request_schedule_time_input(send_message_async, chat_id, scenario, environment)
            else:
                try:
                    minutes = int(minutes_str)
                    await handle_robot_schedule_create(send_message_async, chat_id, scenario, minutes, environment, message_id)
                except ValueError:
                    pass
    elif data.startswith("robot_cancel_"):
        # robot_cancel_abc12345
        task_id = data.replace("robot_cancel_", "")
        await handle_robot_cancel_scheduled(send_message_async, chat_id, task_id, message_id)

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
        "version": "5.4.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Warehouse Telegram Bot",
        "version": "5.4.0",
        "description": "CI/CD notifications, PM dashboard, robot control and full orchestration 🚀"
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


# =============================================================================
# Robot Notifications (уведомления от Warehouse Robot)
# =============================================================================

class RobotNotification(BaseModel):
    """Модель уведомления от робота."""
    scenario: str
    result: Dict[str, Any]


@app.post("/robot/notify")
async def robot_notify(notification: RobotNotification):
    """
    Обработка уведомлений от Warehouse Robot.

    Робот отправляет уведомления о завершении сценариев:
    - receiving: приёмка товара
    - shipping: отгрузка
    - inventory: инвентаризация
    """
    try:
        logger.info(f"Received robot notification: scenario={notification.scenario}")

        # Форматируем сообщение
        message = format_robot_notification(notification.scenario, notification.result)

        # Отправляем в Telegram
        await send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )

        logger.info(f"Robot notification sent successfully")
        return {"status": "ok", "message": "Notification sent"}

    except Exception as e:
        logger.error(f"Robot notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
