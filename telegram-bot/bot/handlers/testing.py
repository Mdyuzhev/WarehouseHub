"""
Обработчики QA команд.
E2E тесты, UI тесты и нагрузочное тестирование! 🔬
"""

import asyncio
from datetime import datetime
from bot.telegram import send_message_with_reply_keyboard, send_message_with_inline_keyboard, send_message, send_chat_action
from bot.keyboards import (
    get_reply_keyboard, get_qa_menu_keyboard, get_qa_type_keyboard, get_qa_action_keyboard,
    get_load_test_keyboard, get_duration_keyboard, get_rampup_keyboard
)
from bot.messages import get_random_joke, format_load_test_stats, format_test_report
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
# Allure Project IDs
# =============================================================================
ALLURE_PROJECTS = {
    "e2e_staging": "e2e-staging",
    "e2e_prod": "e2e-prod",
    "ui_staging": "ui-staging",
    "ui_prod": "ui-prod",
}

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


# =============================================================================
# QA Menu
# =============================================================================

async def handle_qa_menu(chat_id: int):
    """Показывает главное меню QA — выбор среды."""
    msg = """
<b>🔬 QA — Тестирование</b>

Выбери среду для тестирования:
    """
    await send_message_with_inline_keyboard(msg.strip(), get_qa_menu_keyboard(), chat_id=chat_id)


async def handle_qa_env(chat_id: int, env: str):
    """Показывает меню выбора типа теста для среды."""
    env_emoji = "🧪" if env == "staging" else "🚀"
    env_name = "STAGING" if env == "staging" else "PRODUCTION"
    warning = "\n\n⚠️ <b>Внимание!</b> Это боевой сервер!" if env == "prod" else ""

    msg = f"""
<b>{env_emoji} {env_name}</b>{warning}

Выбери тип тестирования:
    """
    await send_message_with_inline_keyboard(msg.strip(), get_qa_type_keyboard(env), chat_id=chat_id)


async def handle_qa_test_type(chat_id: int, test_type: str, env: str):
    """Показывает меню действий для выбранного теста."""
    type_names = {"e2e": "📝 E2E тесты", "ui": "🎭 UI тесты", "load": "🔥 Нагрузка"}
    env_names = {"staging": "🧪 STAGING", "prod": "🚀 PROD"}

    type_name = type_names.get(test_type, test_type)
    env_name = env_names.get(env, env)

    msg = f"""
<b>{type_name}</b>
<i>Среда: {env_name}</i>

Выбери действие:
    """
    await send_message_with_inline_keyboard(msg.strip(), get_qa_action_keyboard(test_type, env), chat_id=chat_id)


# =============================================================================
# E2E & UI Tests
# =============================================================================

async def handle_qa_run(chat_id: int, test_type: str, env: str):
    """Запускает тесты через GitLab CI."""
    # Если это нагрузка — переходим к wizard нагрузки
    if test_type == "load":
        await handle_load_target(chat_id, env)
        return

    # Определяем job для запуска
    job_key = f"run_{test_type}_tests_{env}"
    job_config = GITLAB_JOBS.get(job_key)

    if not job_config:
        await send_message_with_reply_keyboard(
            f"❌ Job не найден: {job_key}",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return

    type_names = {"e2e": "E2E", "ui": "UI"}
    env_names = {"staging": "STAGING", "prod": "PRODUCTION"}
    test_name = type_names.get(test_type, test_type.upper())
    env_name = env_names.get(env, env.upper())

    joke = get_random_joke("e2e_start")

    await send_message_with_reply_keyboard(
        f"{joke}\n\n"
        f"<b>🧪 Запускаю {test_name} тесты на {env_name}...</b>\n\n"
        f"<i>⏳ Это может занять 2-5 минут</i>",
        get_reply_keyboard(),
        chat_id=chat_id
    )

    result = await trigger_gitlab_job(job_config["project"], job_config["job"])

    if result.get("success"):
        job_url = result.get("web_url", "")
        job_id = result.get("job_id")
        project_id = ALLURE_PROJECTS.get(f"{test_type}_{env}", f"{test_type}-{env}")

        await send_message_with_reply_keyboard(
            f"✅ <b>Тесты запущены!</b>\n\n"
            f"<b>Job ID:</b> #{job_id}\n\n"
            f"🔗 <a href=\"{job_url}\">Смотреть в GitLab</a>\n"
            f"📊 <a href=\"{get_allure_report_url(project_id)}\">Allure отчёт</a>\n\n"
            f"<i>Пришлю результат по завершению...</i>",
            get_reply_keyboard(),
            chat_id=chat_id
        )

        # Мониторим тесты
        asyncio.create_task(monitor_test_job(chat_id, job_config["project"], job_id, test_type, env))
    else:
        error = result.get("error", "Unknown error")
        await send_message_with_reply_keyboard(
            f"❌ <b>Не удалось запустить тесты</b>\n\n"
            f"<b>Ошибка:</b> {error}",
            get_reply_keyboard(),
            chat_id=chat_id
        )


async def monitor_test_job(chat_id: int, project: str, job_id: int, test_type: str, env: str):
    """Мониторит тесты и отправляет результат."""
    import logging
    logger = logging.getLogger(__name__)

    max_wait = 600
    check_interval = 20
    elapsed = 0

    project_id = ALLURE_PROJECTS.get(f"{test_type}_{env}", f"{test_type}-{env}")
    type_names = {"e2e": "E2E", "ui": "UI"}
    test_name = type_names.get(test_type, test_type.upper())

    logger.info(f"Starting monitor for job {job_id}, project={project}, test_type={test_type}, env={env}")

    while elapsed < max_wait:
        await asyncio.sleep(check_interval)
        elapsed += check_interval

        result = await get_job_status(project, job_id)
        logger.info(f"Job {job_id} status check: {result}")

        if not result.get("success"):
            logger.warning(f"Failed to get job status: {result.get('error')}")
            continue

        status = result.get("status")

        if status == "success":
            logger.info(f"Job {job_id} SUCCESS! Sending notification...")
            joke = get_random_joke("e2e_success")
            duration = result.get("duration", 0)

            # Пробуем получить детали из Allure
            allure_details = await get_allure_report_details(project_id)
            logger.info(f"Allure details for {project_id}: {allure_details}")

            if allure_details and allure_details.get("statistic"):
                stats = allure_details["statistic"]
                msg = format_test_report(stats, int(duration), test_name, env.upper())
                msg = f"{joke}\n\n{msg}\n\n📊 <a href=\"{get_allure_report_url(project_id)}\">Открыть Allure отчёт</a>"
            else:
                msg = (
                    f"{joke}\n\n"
                    f"<b>✅ {test_name} тесты завершены!</b>\n\n"
                    f"⏱ <b>Время:</b> {int(duration)}с\n\n"
                    f"📊 <a href=\"{get_allure_report_url(project_id)}\">Открыть Allure отчёт</a>"
                )

            await send_message_with_reply_keyboard(msg, get_reply_keyboard(), chat_id=chat_id)
            logger.info(f"Job {job_id} notification sent!")
            return

        elif status == "failed":
            logger.info(f"Job {job_id} FAILED! Sending notification...")
            joke = get_random_joke("e2e_failure")
            await send_message_with_reply_keyboard(
                f"{joke}\n\n"
                f"<b>❌ {test_name} тесты упали!</b>\n\n"
                f"🔗 <a href=\"{result.get('web_url', '')}\">Смотри логи</a>\n"
                f"📊 <a href=\"{get_allure_report_url(project_id)}\">Allure отчёт</a>",
                get_reply_keyboard(),
                chat_id=chat_id
            )
            logger.info(f"Job {job_id} failure notification sent!")
            return

    # Таймаут - тесты не завершились за 10 минут
    logger.warning(f"Job {job_id} TIMEOUT after {max_wait}s!")
    await send_message_with_reply_keyboard(
        f"⏱ <b>Таймаут!</b>\n\n"
        f"{test_name} тесты выполняются дольше 10 минут.\n"
        f"Проверь статус в GitLab.",
        get_reply_keyboard(),
        chat_id=chat_id
    )


async def handle_qa_report(chat_id: int, test_type: str, env: str):
    """Показывает последний отчёт тестов."""
    await send_chat_action(chat_id, "typing")

    project_id = ALLURE_PROJECTS.get(f"{test_type}_{env}", f"{test_type}-{env}")
    type_names = {"e2e": "E2E", "ui": "UI", "load": "Нагрузка"}
    test_name = type_names.get(test_type, test_type.upper())

    details = await get_allure_report_details(project_id)

    if not details or not details.get("statistic"):
        await send_message_with_reply_keyboard(
            f"⚠️ <b>Не удалось получить отчёт</b>\n\n"
            f"<i>Allure Server недоступен или нет данных для {test_name} ({env.upper()}).</i>",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return

    stats = details["statistic"]
    duration = details.get("duration", 0) // 1000  # ms to sec

    msg = format_test_report(stats, duration, test_name, env.upper())
    msg += f"\n\n📊 <a href=\"{get_allure_report_url(project_id)}\">Открыть полный отчёт</a>"

    await send_message_with_reply_keyboard(msg, get_reply_keyboard(), chat_id=chat_id)


# =============================================================================
# Load Testing
# =============================================================================

async def handle_load_menu(chat_id: int):
    """Показывает меню выбора цели для нагрузки (через QA меню)."""
    await handle_qa_menu(chat_id)


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
            "ℹ️ <b>Нет активного теста</b>\n\nНажми 🔬 QA чтобы запустить тестирование.",
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
