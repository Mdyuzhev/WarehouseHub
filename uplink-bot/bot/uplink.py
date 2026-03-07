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
    Отправляет событие деплоя в формате, который ci.mjs обрабатывает нативно.
    """
    if not UPLINK_WEBHOOK_URL:
        return False

    payload = {
        "status": status,
        "commit": {
            "message": commit_message,
            "hash": commit_hash,
            "author": commit_author,
        },
    }
    if elapsed is not None:
        payload["elapsed"] = elapsed
    if error:
        payload["error"] = error

    headers = {"x-deploy-event": "deploy"}
    if UPLINK_WEBHOOK_TOKEN:
        headers["X-Gitlab-Token"] = UPLINK_WEBHOOK_TOKEN

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                UPLINK_WEBHOOK_URL,
                json=payload,
                headers=headers,
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error sending deploy event to Uplink: {e}")
        return False
