"""
Обработчики базовых команд.
/start, /help, /menu, /status, /joke и прочее! 📝
"""

import asyncio
from bot.telegram import send_message_with_reply_keyboard, send_message_with_inline_keyboard, send_chat_action
from bot.keyboards import get_reply_keyboard, get_main_menu_keyboard
from bot.messages import get_random_joke, get_random_dev_joke, format_health_message
from services import check_all_health


async def handle_start(chat_id: int):
    """Обработка команды /start."""
    joke = get_random_joke("start")
    welcome_msg = f"""
{joke}

<b>🤖 Warehouse Bot v5.6</b>

<b>Кнопки внизу:</b>
🏥 статус | 📊 метрики | 🚀 деплой
🔬 QA | 🤖 робот | 📋 PM
❓ помощь

<b>🔬 QA меню (WH-218):</b>
• Среда → E2E / UI / Нагрузка / Очистка
• Wizard для нагрузочного тестирования
• Очистка Redis/Kafka/PostgreSQL

<b>🔐 Деплой и тесты через GitLab CI!</b>
    """
    await send_message_with_reply_keyboard(welcome_msg.strip(), get_reply_keyboard(), chat_id=chat_id)


async def handle_help(chat_id: int):
    """Обработка команды /help."""
    help_msg = """
<b>❓ Справка — Warehouse Bot v5.6</b>

<b>📱 Кнопки внизу:</b>
🏥 статус | 📊 метрики | 🚀 деплой
🔬 QA | 🤖 робот | 📋 PM
❓ помощь

<b>🔬 QA (всё тестирование в одном месте):</b>
• Среда → E2E / UI / Нагрузка / Очистка

<b>🔥 Нагрузочное тестирование:</b>
• Wizard — сценарий → VU → время → паттерн → старт
• Locust (HTTP API), k6 (Kafka)
• VU: 10/25/50, Время: 2/5/10 минут
• Cooldown 30 минут между тестами

<b>🧹 Очистка данных:</b>
• Redis — кэш и сессии
• Kafka — consumer groups
• PostgreSQL — тестовые данные

<b>🤖 Warehouse Robot:</b>
• Приёмка/Отгрузка/Инвентаризация
• Планирование по расписанию

<b>📋 PM Dashboard:</b>
• Аудит сторей, отчёты активности

<b>🚀 Деплой:</b>
/deploy — Staging / Production

<b>📊 Мониторинг:</b>
/status — статус серверов
/release — версия

<i>Бот 24/7, как Redis — всегда в памяти!</i>
    """
    await send_message_with_reply_keyboard(help_msg.strip(), get_reply_keyboard(), chat_id=chat_id)


async def handle_menu(chat_id: int):
    """Обработка команды /menu."""
    await send_message_with_inline_keyboard(
        "📱 <b>Главное меню</b>\n\nВыбери действие:",
        get_main_menu_keyboard(),
        chat_id=chat_id
    )


async def handle_health(chat_id: int):
    """Обработка команды /health или /status."""
    await send_chat_action(chat_id, "typing")

    health_data = await check_all_health()
    message = format_health_message(health_data)

    # Добавляем юмор
    all_up = all(
        s.get("status") == "UP"
        for s in [
            health_data["staging_api"],
            health_data["staging_fe"],
            health_data["prod_api"],
            health_data["prod_fe"]
        ]
    )
    joke = get_random_joke("health_good" if all_up else "health_bad")
    message = f"{joke}\n\n{message}"

    await send_message_with_inline_keyboard(message, get_main_menu_keyboard(), chat_id=chat_id)


async def handle_joke(chat_id: int):
    """Отправляет случайную шутку про разработку."""
    joke = get_random_dev_joke()
    await send_message_with_inline_keyboard(
        f"🎭 <b>Анекдот дня</b>\n\n{joke}",
        get_main_menu_keyboard(),
        chat_id=chat_id
    )


async def handle_metrics(chat_id: int):
    """Показывает метрики K8s."""
    from services import get_k8s_resources

    await send_chat_action(chat_id, "typing")
    k8s = await get_k8s_resources()

    msg = "<b>📊 Метрики кластера K8s</b>\n\n"
    if k8s.get("node"):
        msg += f"💻 CPU: {k8s['node'].get('cpu_percent', 'N/A')}\n"
        msg += f"💾 RAM: {k8s['node'].get('memory_percent', 'N/A')}\n"
    else:
        msg += "<i>Метрики временно недоступны</i>"

    await send_message_with_reply_keyboard(msg, get_reply_keyboard(), chat_id=chat_id)


async def handle_pods(chat_id: int):
    """Показывает статус подов K8s."""
    from services import get_k8s_resources

    await send_chat_action(chat_id, "typing")
    k8s = await get_k8s_resources()

    msg = "<b>📦 Поды Kubernetes</b>\n\n"

    if k8s.get("pods"):
        for pod in k8s["pods"]:
            icon = "🟢" if pod["status"] == "Running" else "🔴" if pod["status"] == "Error" else "🟡"
            restarts = f" (↻{pod['restarts']})" if pod.get('restarts') and pod['restarts'] != "0" else ""
            msg += f"{icon} <code>{pod['name']}</code>{restarts}\n"
    else:
        msg += "<i>Не удалось получить информацию о подах</i>"

    await send_message_with_reply_keyboard(msg.strip(), get_reply_keyboard(), chat_id=chat_id)


async def handle_release(chat_id: int):
    """Показывает версию бота и последние релиз ноутс."""
    msg = """
<b>🚀 Warehouse Bot v5.6.0</b>
<i>Release: 2025-12-02</i>

<b>Что нового в v5.6 (WH-218):</b>

🔬 <b>Unified QA Menu</b>
• Всё тестирование в одном меню: QA → Среда → E2E/UI/Нагрузка/Очистка
• Убраны отдельные кнопки Нагрузка и Очистка
• Упрощённая навигация

<b>v5.5 (WH-217):</b>
• Load Testing Wizard — сценарий → VU → время → старт
• Locust (HTTP) / k6 (Kafka)
• Cleanup Service — Redis/Kafka/PostgreSQL

<b>Предыдущие версии:</b>
• v5.4 — QA Menu, Allure
• v5.2 — Warehouse Robot
• v5.1 — PM Dashboard
    """
    await send_message_with_reply_keyboard(msg.strip(), get_reply_keyboard(), chat_id=chat_id)
