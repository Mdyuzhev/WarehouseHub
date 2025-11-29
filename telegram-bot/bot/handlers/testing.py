"""
Обработчики команд тестирования.
E2E тесты и нагрузочное тестирование! 🧪🔥
"""

import asyncio
from datetime import datetime
from bot.telegram import send_message_with_reply_keyboard, send_message_with_inline_keyboard, send_message, send_chat_action
from bot.keyboards import get_reply_keyboard, get_load_test_keyboard, get_duration_keyboard, get_rampup_keyboard, get_e2e_keyboard
from bot.messages import get_random_joke, format_load_test_stats, format_e2e_report
from services import (
    trigger_gitlab_job, get_job_status,
    start_load_test, stop_load_test, get_load_test_stats, calculate_spawn_rate,
    get_allure_report_details, get_allure_report_url
)
from config import (
    GITLAB_JOBS, STAGING_API_URL, PROD_API_URL, ALLURE_SERVER_URL,
    LOAD_TEST_PASSWORD, LOAD_TEST_GUEST_PASSWORD,
    GUEST_MAX_USERS, GUEST_MAX_DURATION
)

# =============================================================================
# State - состояния для тестирования
# =============================================================================

# Нагрузочное тестирование
load_test_status = {
    "running": False,
    "started_at": None,
    "target": None,
    "users": 0,
    "duration": 0,
    "chat_id": None,
    "stats_task": None,
}

# Ожидание пароля
pending_load_auth = {}

# Wizard настройки НТ
load_test_wizard = {}


# =============================================================================
# E2E Testing
# =============================================================================

async def handle_e2e_menu(chat_id: int):
    """Показывает меню E2E тестов."""
    msg = """
<b>🧪 E2E Тестирование</b>

Запуск E2E тестов через GitLab CI.
Результаты будут в Allure отчёте.
    """
    await send_message_with_inline_keyboard(msg.strip(), get_e2e_keyboard(), chat_id=chat_id)


async def handle_e2e_run(chat_id: int):
    """Запускает E2E тесты через GitLab CI."""
    job_config = GITLAB_JOBS.get("run_e2e")
    joke = get_random_joke("e2e_start")

    await send_message_with_reply_keyboard(
        f"{joke}\n\n"
        f"<b>🧪 Запускаю E2E тесты...</b>\n\n"
        f"<i>⏳ Это может занять 2-5 минут</i>",
        get_reply_keyboard(),
        chat_id=chat_id
    )

    result = await trigger_gitlab_job(job_config["project"], job_config["job"])

    if result.get("success"):
        job_url = result.get("web_url", "")
        job_id = result.get("job_id")

        await send_message_with_reply_keyboard(
            f"✅ <b>Тесты запущены!</b>\n\n"
            f"<b>Job ID:</b> #{job_id}\n\n"
            f"🔗 <a href=\"{job_url}\">Смотреть в GitLab</a>\n"
            f"📊 <a href=\"{get_allure_report_url()}\">Allure отчёт</a>\n\n"
            f"<i>Пришлю результат по завершению...</i>",
            get_reply_keyboard(),
            chat_id=chat_id
        )

        # Мониторим тесты
        asyncio.create_task(monitor_e2e_job(chat_id, job_config["project"], job_id))
    else:
        error = result.get("error", "Unknown error")
        await send_message_with_reply_keyboard(
            f"❌ <b>Не удалось запустить тесты</b>\n\n"
            f"<b>Ошибка:</b> {error}",
            get_reply_keyboard(),
            chat_id=chat_id
        )


async def monitor_e2e_job(chat_id: int, project: str, job_id: int):
    """Мониторит E2E тесты и отправляет результат."""
    max_wait = 600
    check_interval = 20
    elapsed = 0

    while elapsed < max_wait:
        await asyncio.sleep(check_interval)
        elapsed += check_interval

        result = await get_job_status(project, job_id)
        if not result.get("success"):
            continue

        status = result.get("status")

        if status == "success":
            joke = get_random_joke("e2e_success")
            duration = result.get("duration", 0)

            # Пробуем получить детали из Allure
            allure_details = await get_allure_report_details()
            if allure_details and allure_details.get("statistic"):
                stats = allure_details["statistic"]
                msg = format_e2e_report(stats, int(duration))
                msg = f"{joke}\n\n{msg}\n\n📊 <a href=\"{get_allure_report_url()}\">Открыть Allure отчёт</a>"
            else:
                msg = (
                    f"{joke}\n\n"
                    f"<b>✅ E2E тесты завершены!</b>\n\n"
                    f"⏱ <b>Время:</b> {int(duration)}с\n\n"
                    f"📊 <a href=\"{get_allure_report_url()}\">Открыть Allure отчёт</a>"
                )

            await send_message_with_reply_keyboard(msg, get_reply_keyboard(), chat_id=chat_id)
            return

        elif status == "failed":
            joke = get_random_joke("e2e_failure")
            await send_message_with_reply_keyboard(
                f"{joke}\n\n"
                f"<b>❌ E2E тесты упали!</b>\n\n"
                f"🔗 <a href=\"{result.get('web_url', '')}\">Смотри логи</a>\n"
                f"📊 <a href=\"{get_allure_report_url()}\">Allure отчёт</a>",
                get_reply_keyboard(),
                chat_id=chat_id
            )
            return


async def handle_e2e_report(chat_id: int):
    """Показывает последний отчёт E2E тестов."""
    await send_chat_action(chat_id, "typing")

    details = await get_allure_report_details()

    if not details or not details.get("statistic"):
        await send_message_with_reply_keyboard(
            "⚠️ <b>Не удалось получить отчёт</b>\n\n<i>Allure Server недоступен или нет данных.</i>",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return

    stats = details["statistic"]
    duration = details.get("duration", 0) // 1000  # ms to sec

    msg = format_e2e_report(stats, duration)
    msg += f"\n\n📊 <a href=\"{get_allure_report_url()}\">Открыть полный отчёт</a>"

    await send_message_with_reply_keyboard(msg, get_reply_keyboard(), chat_id=chat_id)


# =============================================================================
# Load Testing
# =============================================================================

async def handle_load_menu(chat_id: int):
    """Показывает меню выбора цели для нагрузки."""
    msg = """
<b>🔥 Нагрузочное тестирование</b>

⚠️ <b>Внимание:</b> Для запуска потребуется пароль!

Выбери цель для тестирования:
    """
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🧪 STAGING", "callback_data": "load_staging"},
                {"text": "🚀 PRODUCTION", "callback_data": "load_prod"},
            ],
            [{"text": "⬅️ Назад в меню", "callback_data": "menu"}],
        ]
    }
    await send_message_with_inline_keyboard(msg.strip(), keyboard, chat_id=chat_id)


async def handle_load_target(chat_id: int, target: str):
    """Показывает выбор пользователей для НТ."""
    target_name = "🧪 STAGING" if target == "staging" else "🚀 PRODUCTION"
    warning = "\n⚠️ <b>ВНИМАНИЕ!</b> Это боевой сервер!" if target == "prod" else ""

    msg = f"""
<b>👥 Шаг 1/3: Количество пользователей</b>

📍 Цель: <b>{target_name}</b>{warning}

Выбери количество виртуальных пользователей:
    """
    await send_message_with_inline_keyboard(msg.strip(), get_load_test_keyboard(target), chat_id=chat_id)


async def handle_load_users(chat_id: int, target: str, users: int):
    """Показывает выбор длительности."""
    target_name = "🧪 STAGING" if target == "staging" else "🚀 PRODUCTION"

    msg = f"""
<b>⏱ Шаг 2/3: Длительность теста</b>

📍 Цель: {target_name}
👥 Пользователей: <b>{users}</b>

Выбери длительность теста:
    """
    await send_message_with_inline_keyboard(msg.strip(), get_duration_keyboard(target, users), chat_id=chat_id)


async def handle_load_duration(chat_id: int, target: str, users: int, duration: int):
    """Показывает выбор паттерна нагрузки."""
    target_name = "🧪 STAGING" if target == "staging" else "🚀 PRODUCTION"
    duration_min = duration // 60

    msg = f"""
<b>📊 Шаг 3/3: Паттерн нагрузки</b>

📍 Цель: {target_name}
👥 Пользователей: <b>{users}</b>
⏱ Длительность: <b>{duration_min} мин</b>

Выбери как нарастает нагрузка:

📈 <b>Плавный</b> - {users // 10 or 1} user/сек (рекомендуется)
⚡ <b>Быстрый</b> - {users // 5 or 1} user/сек
🚀 <b>Мгновенный</b> - все сразу (стресс-тест!)
📊 <b>Ступенчатый</b> - по 25% каждые 25% времени
    """
    await send_message_with_inline_keyboard(msg.strip(), get_rampup_keyboard(target, users, duration), chat_id=chat_id)


async def request_password(chat_id: int, target: str, users: int, duration: int, ramp_up: str):
    """Запрашивает пароль для запуска НТ."""
    global pending_load_auth

    if load_test_status["running"]:
        await send_message_with_reply_keyboard(
            "⚠️ <b>Тест уже запущен!</b>\n\nСначала остановите текущий тест кнопкой 🛑",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return

    pending_load_auth[chat_id] = {
        "target": target,
        "users": users,
        "duration": duration,
        "ramp_up": ramp_up
    }

    target_name = "🧪 STAGING" if target == "staging" else "🚀 PRODUCTION"
    duration_min = duration // 60
    ramp_names = {
        "smooth": "📈 Плавный",
        "fast": "⚡ Быстрый",
        "instant": "🚀 Мгновенный",
        "step": "📊 Ступенчатый"
    }
    ramp_name = ramp_names.get(ramp_up, ramp_up)

    msg = f"""
<b>🔐 Требуется авторизация</b>

<b>Параметры теста:</b>
📍 Цель: {target_name}
👥 Пользователей: <b>{users}</b>
⏱ Длительность: <b>{duration_min} мин</b>
📊 Нарастание: <b>{ramp_name}</b>

<b>Введи пароль для запуска:</b>

<i>⏱ У тебя 60 секунд...</i>
    """
    await send_message(msg.strip(), chat_id=chat_id)

    # Автоматически очищаем ожидание через 60 секунд
    asyncio.create_task(clear_pending_auth(chat_id, 60))


async def clear_pending_auth(chat_id: int, seconds: int):
    """Очищает ожидание пароля."""
    await asyncio.sleep(seconds)
    if chat_id in pending_load_auth:
        del pending_load_auth[chat_id]
        await send_message_with_reply_keyboard(
            "⏱ <b>Время вышло!</b>\n\nЗапрос на нагрузочное тестирование отменён.",
            get_reply_keyboard(),
            chat_id=chat_id
        )


async def handle_password_input(chat_id: int, password: str):
    """Обрабатывает ввод пароля для НТ."""
    global pending_load_auth

    if chat_id not in pending_load_auth:
        return False

    auth_data = pending_load_auth[chat_id]

    if password == LOAD_TEST_PASSWORD:
        # Админский пароль
        del pending_load_auth[chat_id]
        await send_message(
            "✅ <b>Пароль принят!</b> (полный доступ)\n\n<i>Запускаю нагрузочное тестирование...</i>",
            chat_id=chat_id
        )
        await start_load_test_confirmed(
            chat_id,
            auth_data["target"],
            auth_data["users"],
            auth_data["duration"],
            auth_data["ramp_up"]
        )
        return True

    elif password == LOAD_TEST_GUEST_PASSWORD:
        # Гостевой пароль
        del pending_load_auth[chat_id]

        users = min(auth_data["users"], GUEST_MAX_USERS)
        duration = min(auth_data["duration"], GUEST_MAX_DURATION)

        if users < auth_data["users"] or duration < auth_data["duration"]:
            await send_message(
                f"✅ <b>Гостевой доступ!</b>\n\n"
                f"⚠️ <i>Параметры ограничены:</i>\n"
                f"👥 Пользователей: {auth_data['users']} → <b>{users}</b>\n"
                f"⏱ Длительность: {auth_data['duration'] // 60} мин → <b>{duration // 60}</b> мин\n\n"
                f"<i>Запускаю...</i>",
                chat_id=chat_id
            )
        else:
            await send_message(
                "✅ <b>Гостевой доступ!</b>\n\n<i>Запускаю нагрузочное тестирование...</i>",
                chat_id=chat_id
            )

        await start_load_test_confirmed(
            chat_id,
            auth_data["target"],
            users,
            duration,
            auth_data["ramp_up"],
            is_guest=True
        )
        return True

    else:
        # Неверный пароль
        del pending_load_auth[chat_id]
        await send_message_with_reply_keyboard(
            "❌ <b>Неверный пароль!</b>\n\n<i>Доступ к нагрузочному тестированию запрещён.</i>\n\n🔒 Если забыл пароль - спроси у админа 😏",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return True


async def start_load_test_confirmed(chat_id: int, target: str, users: int, duration: int, ramp_up: str, is_guest: bool = False):
    """Запускает НТ после подтверждения паролем."""
    global load_test_status

    if load_test_status["running"]:
        await send_message_with_reply_keyboard(
            "⚠️ <b>Тест уже запущен!</b>",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return

    target_url = STAGING_API_URL if target == "staging" else PROD_API_URL
    target_name = "🧪 STAGING" if target == "staging" else "🚀 PRODUCTION"
    spawn_rate = calculate_spawn_rate(users, ramp_up)

    joke = get_random_joke("load_test_start")

    result = await start_load_test(target_url, users, spawn_rate)

    if result.get("success"):
        load_test_status = {
            "running": True,
            "started_at": datetime.now(),
            "target": target,
            "users": users,
            "duration": duration,
            "chat_id": chat_id,
            "stats_task": None,
        }

        duration_min = duration // 60
        access_type = "👤 Гостевой" if is_guest else "👑 Полный"

        await send_message_with_reply_keyboard(
            f"{joke}\n\n"
            f"<b>🔥 Нагрузочный тест запущен!</b>\n\n"
            f"📍 Цель: {target_name}\n"
            f"👥 Пользователей: {users}\n"
            f"⏱ Длительность: {duration_min} мин\n"
            f"🔑 Доступ: {access_type}\n\n"
            f"<i>Буду присылать статистику каждые 3 минуты...</i>",
            get_reply_keyboard(),
            chat_id=chat_id
        )

        # Запускаем мониторинг
        load_test_status["stats_task"] = asyncio.create_task(
            monitor_load_test(chat_id, target, users, duration)
        )
    else:
        await send_message_with_reply_keyboard(
            f"❌ <b>Не удалось запустить тест</b>\n\n<b>Ошибка:</b> {result.get('error', 'Unknown')}",
            get_reply_keyboard(),
            chat_id=chat_id
        )


async def monitor_load_test(chat_id: int, target: str, users: int, duration: int):
    """Мониторит НТ и шлёт статистику."""
    global load_test_status

    stats_interval = 180  # 3 минуты
    elapsed = 0

    while elapsed < duration and load_test_status["running"]:
        await asyncio.sleep(stats_interval)
        elapsed += stats_interval

        if not load_test_status["running"]:
            break

        stats = await get_load_test_stats()
        if stats.get("success"):
            msg = format_load_test_stats(stats, target, users, duration, elapsed)
            await send_message_with_reply_keyboard(msg, get_reply_keyboard(), chat_id=chat_id)

    # Финальный отчёт
    if load_test_status["running"]:
        await handle_stop_load_test(chat_id, auto_stop=True)


async def handle_stop_load_test(chat_id: int, auto_stop: bool = False):
    """Останавливает НТ."""
    global load_test_status

    if not load_test_status["running"]:
        await send_message_with_reply_keyboard(
            "ℹ️ <b>Нет активного теста</b>",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return

    result = await stop_load_test()
    stats = await get_load_test_stats()

    joke = get_random_joke("load_test_stop")
    elapsed = 0
    if load_test_status["started_at"]:
        elapsed = int((datetime.now() - load_test_status["started_at"]).total_seconds())

    # Финальный отчёт
    msg = f"{joke}\n\n<b>🏁 ФИНАЛЬНЫЙ ОТЧЁТ</b>\n\n"

    if stats.get("success"):
        msg += format_load_test_stats(
            stats,
            load_test_status["target"],
            load_test_status["users"],
            load_test_status["duration"],
            elapsed
        )
    else:
        msg += f"⏱ <b>Время:</b> {elapsed // 60}м {elapsed % 60}с"

    if auto_stop:
        msg += "\n\n<i>Тест завершился по таймеру</i>"

    # Сбрасываем статус
    if load_test_status["stats_task"]:
        load_test_status["stats_task"].cancel()

    load_test_status = {
        "running": False,
        "started_at": None,
        "target": None,
        "users": 0,
        "duration": 0,
        "chat_id": None,
        "stats_task": None,
    }

    await send_message_with_reply_keyboard(msg, get_reply_keyboard(), chat_id=chat_id)


async def handle_load_status(chat_id: int):
    """Показывает текущий статус НТ."""
    if not load_test_status["running"]:
        await send_message_with_reply_keyboard(
            "ℹ️ <b>Нет активного теста</b>\n\nНажми 🔥 чтобы запустить нагрузочное тестирование.",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return

    await send_chat_action(chat_id, "typing")

    stats = await get_load_test_stats()
    elapsed = 0
    if load_test_status["started_at"]:
        elapsed = int((datetime.now() - load_test_status["started_at"]).total_seconds())

    if stats.get("success"):
        msg = format_load_test_stats(
            stats,
            load_test_status["target"],
            load_test_status["users"],
            load_test_status["duration"],
            elapsed
        )
    else:
        target_name = "🧪 STAGING" if load_test_status["target"] == "staging" else "🚀 PRODUCTION"
        msg = (
            f"<b>🔥 Тест запущен</b>\n\n"
            f"📍 Цель: {target_name}\n"
            f"👥 Пользователей: {load_test_status['users']}\n"
            f"⏱ Прошло: {elapsed // 60}м {elapsed % 60}с\n\n"
            f"<i>Статистика пока недоступна</i>"
        )

    await send_message_with_reply_keyboard(msg, get_reply_keyboard(), chat_id=chat_id)


def is_pending_password(chat_id: int) -> bool:
    """Проверяет, ожидается ли пароль от пользователя."""
    return chat_id in pending_load_auth


def is_pending_wizard(chat_id: int) -> bool:
    """Проверяет, в wizard ли пользователь."""
    return chat_id in load_test_wizard
