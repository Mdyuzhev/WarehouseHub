"""
Клиент для отправки уведомлений в Uplink через botservice webhook API.
Аналог bot/telegram.py из telegram-bot, но для Matrix.
"""

import logging
import httpx
from config import UPLINK_WEBHOOK_URL, UPLINK_WEBHOOK_TOKEN

logger = logging.getLogger(__name__)


async def send_message(text: str, html: str = None) -> bool:
    """
    Отправляет уведомление в Uplink.

    text  — plaintext fallback.
    html  — HTML-версия для Matrix-клиентов (опциональна).
    """
    if not UPLINK_WEBHOOK_URL:
        logger.warning("UPLINK_WEBHOOK_URL not set, skipping notification")
        return False

    payload = {
        "object_kind": "notify",
        "text": text,
        "html": html or text,
    }

    headers = {"Content-Type": "application/json"}
    if UPLINK_WEBHOOK_TOKEN:
        headers["X-Gitlab-Token"] = UPLINK_WEBHOOK_TOKEN

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                UPLINK_WEBHOOK_URL,
                json=payload,
                headers=headers,
            )
            if response.status_code == 200:
                logger.info("Message sent to Uplink successfully")
                return True
            else:
                logger.error(f"Uplink webhook returned {response.status_code}: {response.text}")
                return False
    except httpx.TimeoutException:
        logger.warning("Timeout sending notification to Uplink")
        return False
    except Exception as e:
        logger.error(f"Error sending to Uplink: {e}")
        return False


async def send_deploy_event(
    status: str,
    commit_message: str = "",
    commit_hash: str = "",
    commit_author: str = "",
    elapsed: float = None,
    error: str = None,
) -> bool:
    """
    Форматирует и отправляет событие деплоя как HTML-сообщение.
    """
    if status == "success":
        emoji = "🚀"
        title = "Деплой WarehouseHub успешен"
    else:
        emoji = "💥"
        title = "Деплой WarehouseHub провален"

    html = f"<b>{emoji} {title}</b>"
    if commit_hash or commit_message:
        short_hash = commit_hash[:7] if commit_hash else ""
        html += f"<br/>📦 <code>{short_hash}</code> {commit_message}"
        if commit_author:
            html += f" <i>by {commit_author}</i>"
    if elapsed is not None:
        html += f"<br/>⏱ {elapsed:.0f}s"
    if error:
        html += f"<br/>🔴 {error}"

    plain = f"{'🚀' if status == 'success' else '💥'} Deploy {status}"
    if commit_hash:
        plain += f" — {commit_hash[:7]} {commit_message}"

    return await send_message(text=plain, html=html)
