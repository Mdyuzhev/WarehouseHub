"""
GitLab Webhook Handler.
Обрабатывает события от GitLab и шлёт уведомления! 🚀

События:
- Pipeline: started, success, failed
- Job: started, success, failed (с логами при падении)

Улучшения WH-88:
- Парсинг WH-xxx из веток и коммитов
- Показ информации о задаче в уведомлениях
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
from services.youtrack import parse_issue_id, get_issue_by_id
from config import TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


# Кэш информации о задачах чтобы не дёргать YouTrack на каждый webhook
_issue_cache = {}


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


async def get_issue_info(issue_id: str) -> Optional[dict]:
    """
    Получает информацию о задаче (с кэшированием).

    Args:
        issue_id: ID задачи (WH-xxx)

    Returns:
        dict с информацией или None
    """
    global _issue_cache

    if issue_id in _issue_cache:
        return _issue_cache[issue_id]

    result = await get_issue_by_id(issue_id)
    if result.get("success"):
        _issue_cache[issue_id] = result.get("issue")
        return result.get("issue")

    return None


def format_issue_info(issue: dict) -> str:
    """Форматирует краткую информацию о задаче для добавления в сообщение."""
    if not issue:
        return ""

    state_emoji = {
        "Open": "📋",
        "In Progress": "🔄",
        "In Review": "👀",
        "Done": "✅",
        "Verified": "✔️"
    }.get(issue.get("state", ""), "❓")

    summary = issue.get("summary", "")
    if len(summary) > 60:
        summary = summary[:60] + "..."

    return f"\n\n📌 <b>Задача {issue.get('id', '')}:</b>\n{state_emoji} {summary}"


async def handle_pipeline_event(data: dict):
    """
    Обрабатывает события pipeline.

    Редизайн WH-120:
    - running: краткое уведомление
    - success/failed/canceled: полное уведомление
    - Добавляем ссылку на YouTrack если есть WH-xxx
    """
    status = data.get("object_attributes", {}).get("status", "unknown")

    # Отправляем уведомление только на важные статусы
    if status in ["running", "success", "failed", "canceled"]:
        message = format_pipeline_message(data)

        # Ищем WH-xxx в ветке (только для завершённых)
        if status in ["success", "failed", "canceled"]:
            ref = data.get("object_attributes", {}).get("ref", "")
            issue_id = parse_issue_id(ref)

            if issue_id:
                issue = await get_issue_info(issue_id)
                if issue:
                    message += format_issue_info(issue)
                    message += f"\n<a href=\"http://192.168.1.74:8088/issue/{issue_id}\">→ YouTrack</a>"

        await send_message(message, chat_id=TELEGRAM_CHAT_ID)
        logger.info(f"Pipeline {status}" + (f" ({issue_id})" if status != "running" and 'issue_id' in dir() and issue_id else ""))
    else:
        logger.debug(f"Skipping pipeline status: {status}")


async def handle_job_event(data: dict):
    """
    Обрабатывает события job (build).

    Редизайн WH-120:
    - running: НЕ отправляем (слишком много шума, pipeline running достаточно)
    - success: только для deploy jobs
    - failed: всегда отправляем с логами
    """
    status = data.get("build_status", "unknown")
    job_id = data.get("build_id")
    job_name = data.get("build_name", "")
    project_id = data.get("project_id")

    # Фильтрация по типу job
    is_deploy_job = "deploy" in job_name.lower()

    # Пропускаем running - достаточно pipeline running
    if status == "running":
        logger.debug(f"Skipping job running: {job_name}")
        return

    # Для success - только deploy jobs
    if status == "success" and not is_deploy_job:
        logger.debug(f"Skipping non-deploy job success: {job_name}")
        return

    # Отправляем уведомление
    if status in ["success", "failed", "canceled"]:

        # Если failed - получаем логи
        if status == "failed" and job_id and project_id:
            log_result = await get_job_trace(project_id, job_id, lines=20)

            if log_result.get("success"):
                log = log_result.get("log", "Лог недоступен")
                message = format_job_failed_with_log(data, log)
            else:
                message = format_job_message(data)
                message += "\n\n<i>⚠️ Лог недоступен</i>"
        else:
            message = format_job_message(data)

        # Ищем WH-xxx в ветке (только для failed)
        if status == "failed":
            ref = data.get("ref", "")
            issue_id = parse_issue_id(ref)

            if issue_id:
                issue = await get_issue_info(issue_id)
                if issue:
                    message += format_issue_info(issue)
                    message += f"\n<a href=\"http://192.168.1.74:8088/issue/{issue_id}\">→ YouTrack</a>"

        await send_message(message, chat_id=TELEGRAM_CHAT_ID)
        logger.info(f"Job {status}: {job_name}")
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
