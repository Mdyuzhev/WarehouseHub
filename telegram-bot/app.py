"""
Warehouse Telegram Bot v7.0
Docker-compose environment. Minimal: status, metrics, robot, help.
"""

import asyncio
import signal
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    LOG_FORMAT, LOG_LEVEL,
    GRACEFUL_SHUTDOWN_TIMEOUT, MAX_BACKOFF_SECONDS, INITIAL_BACKOFF_SECONDS
)
from bot.telegram import (
    get_updates, send_message_with_reply_keyboard, answer_callback_query,
    send_message_with_inline_keyboard, edit_message_text, send_message,
    delete_webhook
)
from bot.keyboards import get_reply_keyboard, get_main_menu_keyboard
from bot.messages import format_robot_notification
from bot.handlers import (
    handle_start, handle_help, handle_menu, handle_health, handle_metrics, handle_pods,
    handle_robot_menu, handle_robot_status, handle_robot_stats,
    handle_robot_scenarios, handle_robot_duration_select, handle_robot_start, handle_robot_stop,
    handle_robot_speed_select, handle_robot_environment_select,
    request_robot_password, handle_robot_password_input,
    is_pending_robot_password,
    handle_robot_schedule_menu, handle_robot_schedule_env, handle_robot_schedule_time,
    handle_robot_schedule_create, handle_robot_scheduled_list, handle_robot_cancel_scheduled,
    request_schedule_time_input, handle_schedule_time_input, is_pending_schedule_time,
)


# =============================================================================
# Logging
# =============================================================================
def setup_logging():
    import json
    import sys

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "service": "telegram-bot",
                "version": "7.0.0"
            }
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_obj, ensure_ascii=False)

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

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

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger(__name__)

last_update_id = 0
shutdown_event = asyncio.Event()
polling_task = None


# =============================================================================
# FastAPI App
# =============================================================================

def handle_shutdown(signum, frame):
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global polling_task

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    # Delete webhook to ensure polling works
    await delete_webhook()

    logger.info("Bot started with polling")
    polling_task = asyncio.create_task(telegram_polling())

    yield

    logger.info("Initiating graceful shutdown...")
    shutdown_event.set()

    if polling_task:
        try:
            await asyncio.wait_for(polling_task, timeout=GRACEFUL_SHUTDOWN_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("Polling task did not stop in time, cancelling...")
            polling_task.cancel()

    logger.info("Bot stopped gracefully")


app = FastAPI(
    title="Warehouse Telegram Bot",
    description="Status, metrics, robot control",
    version="7.0.0",
    lifespan=lifespan
)


# =============================================================================
# Telegram Polling
# =============================================================================

async def telegram_polling():
    global last_update_id
    consecutive_errors = 0

    while not shutdown_event.is_set():
        try:
            updates = await get_updates(offset=last_update_id + 1)

            if updates is not None:
                consecutive_errors = 0

            for update in updates:
                if shutdown_event.is_set():
                    break

                last_update_id = update.get("update_id", last_update_id)

                if "callback_query" in update:
                    await process_callback(update["callback_query"])
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
            backoff = min(INITIAL_BACKOFF_SECONDS * (2 ** (consecutive_errors - 1)), MAX_BACKOFF_SECONDS)
            logger.error(f"Polling error (attempt {consecutive_errors}): {e}")

            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=backoff)
                break
            except asyncio.TimeoutError:
                pass

    logger.info("Polling loop stopped")


async def process_command(chat_id: int, text: str):
    """Main command router."""
    log_text = "[HIDDEN]" if is_pending_robot_password(chat_id) else text
    logger.info(f"Command received: chat_id={chat_id}, text='{log_text}'")

    # Pending input states
    if is_pending_robot_password(chat_id):
        await handle_robot_password_input(send_message_async, chat_id, text)
        return

    if is_pending_schedule_time(chat_id):
        await handle_schedule_time_input(send_message_async, chat_id, text)
        return

    # Reply keyboard buttons
    if text == "🏥 Статус":
        await handle_health(chat_id)
    elif text == "📊 Метрики":
        await handle_metrics(chat_id)
    elif text in ["🤖 Robot", "/robot"]:
        await handle_robot_menu(send_message_async, chat_id)
    elif text in ["❓", "❓ Помощь"]:
        await handle_help(chat_id)

    # Slash commands
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


async def send_message_async(
    chat_id: int,
    text: str,
    parse_mode: str = "Markdown",
    reply_markup: dict = None,
    edit_message_id: int = None
):
    if edit_message_id:
        return await edit_message_text(
            chat_id=chat_id, message_id=edit_message_id,
            text=text, keyboard=reply_markup, parse_mode=parse_mode
        )
    elif reply_markup:
        return await send_message_with_inline_keyboard(
            chat_id=chat_id, text=text,
            keyboard=reply_markup, parse_mode=parse_mode
        )
    else:
        return await send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)


async def process_callback(callback_query: dict):
    """Inline button handler."""
    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")

    if not chat_id:
        return

    await answer_callback_query(callback_id)

    if data == "health":
        await handle_health(chat_id)
    elif data == "metrics":
        await handle_metrics(chat_id)
    elif data == "menu":
        await handle_menu(chat_id)
    elif data == "help":
        await handle_help(chat_id)

    # Robot
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
        scenario = data.replace("robot_run_", "")
        await handle_robot_duration_select(send_message_async, chat_id, scenario, message_id)
    elif data.startswith("robot_dur_"):
        parts = data.replace("robot_dur_", "").rsplit("_", 1)
        if len(parts) == 2:
            scenario, duration_str = parts
            await handle_robot_environment_select(send_message_async, chat_id, scenario, int(duration_str), message_id)
    elif data.startswith("robot_env_"):
        parts = data.replace("robot_env_", "").rsplit("_", 2)
        if len(parts) == 3:
            scenario, duration_str, environment = parts
            await request_robot_password(send_message_async, chat_id, scenario, int(duration_str), environment)
    elif data.startswith("robot_speed_"):
        parts = data.replace("robot_speed_", "").rsplit("_", 3)
        if len(parts) == 4:
            scenario, duration_str, environment, speed = parts
            await handle_robot_start(send_message_async, chat_id, scenario, int(duration_str), speed, environment, message_id)

    # Robot Schedule
    elif data == "robot_schedule":
        await handle_robot_schedule_menu(send_message_async, chat_id, message_id)
    elif data == "robot_scheduled":
        await handle_robot_scheduled_list(send_message_async, chat_id, message_id)
    elif data.startswith("robot_sched_"):
        scenario = data.replace("robot_sched_", "")
        await handle_robot_schedule_env(send_message_async, chat_id, scenario, message_id)
    elif data.startswith("robot_schedenv_"):
        parts = data.replace("robot_schedenv_", "").rsplit("_", 1)
        if len(parts) == 2:
            scenario, environment = parts
            await handle_robot_schedule_time(send_message_async, chat_id, scenario, environment, message_id)
    elif data.startswith("robot_time_"):
        parts = data.replace("robot_time_", "").rsplit("_", 2)
        if len(parts) == 3:
            scenario, environment, minutes_str = parts
            if minutes_str == "custom":
                await request_schedule_time_input(send_message_async, chat_id, scenario, environment)
            else:
                try:
                    await handle_robot_schedule_create(send_message_async, chat_id, scenario, int(minutes_str), environment, message_id)
                except ValueError:
                    pass
    elif data.startswith("robot_cancel_"):
        task_id = data.replace("robot_cancel_", "")
        await handle_robot_cancel_scheduled(send_message_async, chat_id, task_id, message_id)

    elif data == "noop":
        pass


# =============================================================================
# HTTP Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "7.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/")
async def root():
    return {
        "name": "Warehouse Telegram Bot",
        "version": "7.0.0",
    }


# =============================================================================
# Robot Notifications
# =============================================================================

class RobotNotification(BaseModel):
    scenario: str
    result: Dict[str, Any]


@app.post("/robot/notify")
async def robot_notify(notification: RobotNotification):
    try:
        logger.info(f"Received robot notification: scenario={notification.scenario}")
        message = format_robot_notification(notification.scenario, notification.result)
        await send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Robot notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
