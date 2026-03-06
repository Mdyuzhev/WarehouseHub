"""
Basic command handlers.
/start, /help, /menu, /status, /metrics, /pods
"""

from bot.telegram import send_message_with_reply_keyboard, send_message_with_inline_keyboard, send_chat_action
from bot.keyboards import get_reply_keyboard, get_main_menu_keyboard
from bot.messages import format_health_message
from services import check_all_health


async def handle_start(chat_id: int):
    welcome_msg = """
<b>🤖 Warehouse Bot v7.0</b>

<b>Кнопки внизу:</b>
🏥 статус | 📊 метрики
🤖 робот | ❓ помощь

<b>Команды:</b>
/status — статус серверов
/pods — сервисы
/robot — управление роботом
/help — справка
    """
    await send_message_with_reply_keyboard(welcome_msg.strip(), get_reply_keyboard(), chat_id=chat_id)


async def handle_help(chat_id: int):
    help_msg = """
<b>❓ Справка — Warehouse Bot v7.0</b>

<b>📱 Кнопки:</b>
🏥 статус | 📊 метрики
🤖 робот | ❓ помощь

<b>🤖 Warehouse Robot:</b>
• Приёмка / Отгрузка / Инвентаризация
• Планирование по расписанию

<b>📊 Мониторинг:</b>
/status — статус серверов
/pods — docker-compose сервисы
/metrics — CPU / RAM
    """
    await send_message_with_reply_keyboard(help_msg.strip(), get_reply_keyboard(), chat_id=chat_id)


async def handle_menu(chat_id: int):
    await send_message_with_inline_keyboard(
        "📱 <b>Главное меню</b>\n\nВыбери действие:",
        get_main_menu_keyboard(),
        chat_id=chat_id
    )


async def handle_health(chat_id: int):
    await send_chat_action(chat_id, "typing")
    health_data = await check_all_health()
    message = format_health_message(health_data)
    await send_message_with_inline_keyboard(message, get_main_menu_keyboard(), chat_id=chat_id)


async def handle_metrics(chat_id: int):
    from services import get_k8s_resources

    await send_chat_action(chat_id, "typing")
    k8s = await get_k8s_resources()

    msg = "<b>📊 Метрики Homelab</b>\n\n"
    if k8s.get("node"):
        msg += f"💻 CPU: {k8s['node'].get('cpu_percent', 'N/A')}\n"
        msg += f"💾 RAM: {k8s['node'].get('memory_percent', 'N/A')}\n"
    else:
        msg += "<i>Метрики временно недоступны</i>"

    await send_message_with_reply_keyboard(msg, get_reply_keyboard(), chat_id=chat_id)


async def handle_pods(chat_id: int):
    from services import get_k8s_resources

    await send_chat_action(chat_id, "typing")
    k8s = await get_k8s_resources()

    msg = "<b>📦 Сервисы Homelab</b>\n\n"

    if k8s.get("pods"):
        for pod in k8s["pods"]:
            icon = "🟢" if pod["status"] == "Running" else "🔴" if pod["status"] == "Error" else "🟡"
            restarts = f" (↻{pod['restarts']})" if pod.get('restarts') and pod['restarts'] != "0" else ""
            msg += f"{icon} <code>{pod['name']}</code>{restarts}\n"
    else:
        msg += "<i>Не удалось получить информацию о сервисах</i>"

    await send_message_with_reply_keyboard(msg.strip(), get_reply_keyboard(), chat_id=chat_id)
