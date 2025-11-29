"""
Низкоуровневая работа с Telegram API.
Всё что нужно для общения с Telegram, без бизнес-логики! 📱
"""

import logging
import httpx
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


async def send_message(
    text: str,
    chat_id: int = None,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True
) -> bool:
    """Отправляет простое текстовое сообщение."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return False

    chat_id = chat_id or TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_web_page_preview,
            })
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return False


async def send_message_with_inline_keyboard(
    text: str,
    keyboard: dict,
    chat_id: int = None,
    parse_mode: str = "HTML"
) -> bool:
    """Отправляет сообщение с inline клавиатурой."""
    if not TELEGRAM_BOT_TOKEN:
        return False

    chat_id = chat_id or TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": keyboard,
                "disable_web_page_preview": True,
            })
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send message with keyboard: {e}")
        return False


async def send_message_with_reply_keyboard(
    text: str,
    keyboard: dict,
    chat_id: int = None,
    parse_mode: str = "HTML"
) -> bool:
    """Отправляет сообщение с reply клавиатурой (кнопки внизу)."""
    if not TELEGRAM_BOT_TOKEN:
        return False

    chat_id = chat_id or TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": keyboard,
                "disable_web_page_preview": True,
            })
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send message with reply keyboard: {e}")
        return False


async def send_chat_action(chat_id: int, action: str = "typing") -> bool:
    """Отправляет действие (typing, upload_photo, etc.)."""
    if not TELEGRAM_BOT_TOKEN:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": chat_id,
                "action": action,
            })
            return response.status_code == 200
    except:
        return False


async def answer_callback_query(callback_id: str, text: str = None) -> bool:
    """Отвечает на callback query (убирает 'часики')."""
    if not TELEGRAM_BOT_TOKEN:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            return response.status_code == 200
    except:
        return False


async def get_updates(offset: int = 0, timeout: int = 30) -> list:
    """Получает обновления от Telegram (long polling)."""
    if not TELEGRAM_BOT_TOKEN:
        return []

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {
        "offset": offset,
        "timeout": timeout,
        "allowed_updates": ["message", "callback_query"]
    }

    try:
        async with httpx.AsyncClient(timeout=timeout + 5) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("result", [])
            elif response.status_code == 409:
                # Конфликт - другой бот использует getUpdates
                logger.warning("Telegram 409 Conflict - waiting...")
                return []
    except Exception as e:
        logger.error(f"Failed to get updates: {e}")

    return []


async def edit_message_text(
    chat_id: int,
    message_id: int,
    text: str,
    keyboard: dict = None,
    parse_mode: str = "HTML"
) -> bool:
    """Редактирует текст сообщения."""
    if not TELEGRAM_BOT_TOKEN:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    if keyboard:
        payload["reply_markup"] = keyboard

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            return response.status_code == 200
    except:
        return False
