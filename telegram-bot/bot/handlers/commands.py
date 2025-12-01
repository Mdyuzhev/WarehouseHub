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

<b>🤖 Warehouse Bot v5.2</b>

<b>Кнопки внизу:</b>
🏥 статус | 📊 метрики | 🚀 деплой
🧪 E2E | 🔥 нагрузка | 🛑 стоп
📋 PM | 🤖 робот | ❓ помощь

<b>🔐 Деплой и тесты через GitLab CI!</b>
    """
    await send_message_with_reply_keyboard(welcome_msg.strip(), get_reply_keyboard(), chat_id=chat_id)


async def handle_help(chat_id: int):
    """Обработка команды /help."""
    help_msg = """
<b>❓ Справка — Warehouse Bot v5.2</b>

<b>📱 Кнопки внизу:</b>
🏥 статус | 📊 метрики | 🚀 деплой
🧪 E2E | 🔥 нагрузка | 🛑 стоп
📋 PM | 🤖 робот | ❓ помощь

<b>🤖 Warehouse Robot:</b>
• Запуск сценариев — Приёмка/Отгрузка/Инвентаризация
• Продолжительность — 5мин/30мин/1час/однократно
• Скорость — пауза между повторами (1с/5с/15с)
• Планирование — запуск по расписанию (МСК)
• Статус и статистика робота

<b>📋 PM Dashboard:</b>
• 🔄 Сейчас в работе — последние задачи агента
• 📋 Аудит сторей — открытые User Stories
• 📈 Отчёт за день/неделю — активность

<b>🚀 Деплой:</b>
/deploy — меню деплоя
Staging: API | Frontend | Всё
Production: API | Frontend | Всё

<b>🧪 Тестирование:</b>
/e2e — E2E тесты (RestAssured)
/load — нагрузочное тестирование (Locust)

<b>📊 Мониторинг:</b>
/status — статус серверов
/pods — поды K8s

<b>ℹ️ Инфо:</b>
/release — версия и что нового

<i>Бот 24/7, в отличие от разрабов...</i> 😏
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
<b>🚀 Warehouse Bot v5.2.0</b>
<i>Release: 2025-12-01</i>

<b>Что нового в v5.2:</b>

🤖 <b>Warehouse Robot</b> — эмуляция складских операций
• Сценарии: Приёмка, Отгрузка, Инвентаризация
• Продолжительность: 5мин / 30мин / 1час / однократно
• Скорость: пауза между повторами (1с/5с/15с)
• Планирование запуска по расписанию (МСК)
• Уведомления с детализацией товаров

📋 <b>PM Dashboard</b>
• 🔄 Сейчас в работе — последние задачи агента
• 📋 Аудит сторей — открытые User Stories
• 📈 Отчёты за день/неделю — активность

<b>Предыдущие версии:</b>
• v5.1.0 — PM Dashboard, YouTrack интеграция
• v5.0.0 — GitLab CI/CD, Locust, E2E, K8s
    """
    await send_message_with_reply_keyboard(msg.strip(), get_reply_keyboard(), chat_id=chat_id)
