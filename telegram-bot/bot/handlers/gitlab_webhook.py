"""
GitLab Webhook Handler.
Обрабатывает события от GitLab и шлёт уведомления! 🚀

События:
- Pipeline: started, success, failed
- Job: started, success, failed (с логами при падении)
"""

import logging
from typing import Optional
from bot.telegram import send_message
from bot.messages import (
    format_pipeline_message,
    format_job_message,
    format_job_failed_with_log
)
from services.gitlab import get_job_trace
from config import TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


async def handle_gitlab_webhook(event_type: str, data: dict) -> dict:
    """
    Главный обработчик GitLab webhooks.

    Args:
        event_type: Тип события (pipeline, build, etc.)
        data: Payload от GitLab

    Returns:
        dict: {"status": "ok"} или {"status": "ignored", "reason": "..."}
    """
    try:
        # Pipeline события
        if event_type == "pipeline":
            await handle_pipeline_event(data)
            return {"status": "ok", "event": "pipeline"}

        # Job (build) события
        elif event_type == "build":
            await handle_job_event(data)
            return {"status": "ok", "event": "build"}

        else:
            logger.info(f"Ignoring event type: {event_type}")
            return {"status": "ignored", "reason": f"Event type '{event_type}' not handled"}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "error": str(e)}


async def handle_pipeline_event(data: dict):
    """
    Обрабатывает события pipeline.

    Отправляем уведомления:
    - running: когда pipeline стартует
    - success: когда успешно завершился
    - failed: когда упал
    """
    status = data.get("object_attributes", {}).get("status", "unknown")

    # Отправляем уведомление только на важные статусы
    if status in ["running", "success", "failed", "canceled"]:
        message = format_pipeline_message(data)
        await send_message(message, chat_id=TELEGRAM_CHAT_ID)
        logger.info(f"Sent pipeline {status} notification")
    else:
        logger.debug(f"Skipping pipeline status: {status}")


async def handle_job_event(data: dict):
    """
    Обрабатывает события job (build).

    Отправляем уведомления:
    - running: когда job стартует
    - success: когда успешно завершился
    - failed: когда упал (с логами!)
    """
    status = data.get("build_status", "unknown")
    job_id = data.get("build_id")
    project_id = data.get("project_id")

    # Отправляем уведомление на важные статусы
    if status in ["running", "success", "failed", "canceled"]:

        # Если failed - получаем логи
        if status == "failed" and job_id and project_id:
            log_result = await get_job_trace(project_id, job_id, lines=20)

            if log_result.get("success"):
                log = log_result.get("log", "Лог недоступен")
                message = format_job_failed_with_log(data, log)
            else:
                # Если не получилось получить лог - просто отправляем обычное сообщение
                message = format_job_message(data)
                message += "\n\n<i>⚠️ Не удалось получить лог</i>"
        else:
            # Для успешных и running - обычное сообщение
            message = format_job_message(data)

        await send_message(message, chat_id=TELEGRAM_CHAT_ID)
        logger.info(f"Sent job {status} notification for job #{job_id}")
    else:
        logger.debug(f"Skipping job status: {status}")


# =============================================================================
# Дополнительные утилиты
# =============================================================================

def should_notify_pipeline(data: dict) -> bool:
    """
    Проверяет, нужно ли уведомлять о pipeline.
    Можно добавить фильтры по проектам, веткам и т.д.
    """
    # Пока уведомляем обо всех
    return True


def should_notify_job(data: dict) -> bool:
    """
    Проверяет, нужно ли уведомлять о job.
    Можно добавить фильтры по именам jobs, стадиям и т.д.
    """
    # Пока уведомляем обо всех
    return True
