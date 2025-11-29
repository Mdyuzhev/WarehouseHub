"""
Обработчики команд деплоя.
Всё что связано с деплоем живёт здесь! 🚀
"""

import asyncio
from bot.telegram import send_message_with_reply_keyboard, send_message_with_inline_keyboard, send_message
from bot.keyboards import get_reply_keyboard, get_deploy_menu_keyboard
from bot.messages import get_random_joke
from services import trigger_gitlab_job, get_job_status
from config import GITLAB_JOBS, DEPLOY_PASSWORD

# =============================================================================
# State - ожидание пароля для деплоя
# =============================================================================
pending_deploy_auth = {}


async def handle_deploy_menu(chat_id: int):
    """Показывает меню деплоя."""
    msg = """
<b>🚀 Меню деплоя</b>

Выбери что и куда деплоить:
    """
    await send_message_with_inline_keyboard(msg.strip(), get_deploy_menu_keyboard(), chat_id=chat_id)


async def request_deploy_password(chat_id: int, job_key: str, component: str, env: str):
    """Запрашивает пароль для деплоя."""
    global pending_deploy_auth

    pending_deploy_auth[chat_id] = {
        "job_key": job_key,
        "component": component,
        "env": env
    }

    env_emoji = "🧪" if env == "staging" else "🚀"
    env_warning = "\n⚠️ <b>ВНИМАНИЕ!</b> Это боевой сервер!" if env == "prod" else ""

    msg = f"""
<b>🔐 Требуется авторизация</b>

<b>Деплой:</b> {component}
<b>Окружение:</b> {env_emoji} {env.upper()}{env_warning}

<b>Введи пароль для деплоя:</b>

<i>⏱ У тебя 60 секунд...</i>
    """
    await send_message(msg.strip(), chat_id=chat_id)

    # Автоматически очищаем ожидание через 60 секунд
    asyncio.create_task(clear_pending_deploy_auth(chat_id, 60))


async def clear_pending_deploy_auth(chat_id: int, seconds: int):
    """Очищает ожидание пароля деплоя."""
    await asyncio.sleep(seconds)
    if chat_id in pending_deploy_auth:
        del pending_deploy_auth[chat_id]
        await send_message_with_reply_keyboard(
            "⏱ <b>Время вышло!</b>\n\nЗапрос на деплой отменён.",
            get_reply_keyboard(),
            chat_id=chat_id
        )


async def handle_deploy_password_input(chat_id: int, password: str):
    """Обрабатывает ввод пароля для деплоя."""
    global pending_deploy_auth

    if chat_id not in pending_deploy_auth:
        return False

    auth_data = pending_deploy_auth[chat_id]

    if password == DEPLOY_PASSWORD:
        del pending_deploy_auth[chat_id]
        await send_message(
            "✅ <b>Пароль принят!</b>\n\n<i>Запускаю деплой...</i>",
            chat_id=chat_id
        )
        await handle_deploy_command(
            chat_id,
            auth_data["job_key"],
            auth_data["component"],
            auth_data["env"]
        )
        return True
    else:
        del pending_deploy_auth[chat_id]
        await send_message_with_reply_keyboard(
            "❌ <b>Неверный пароль!</b>\n\n<i>Деплой отменён.</i>\n\n🔒 Если забыл пароль - спроси у админа 😏",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return True


def is_pending_deploy_password(chat_id: int) -> bool:
    """Проверяет, ожидается ли пароль деплоя от пользователя."""
    return chat_id in pending_deploy_auth


async def handle_deploy_command(chat_id: int, job_key: str, component: str, env: str):
    """Запускает деплой через GitLab CI (после авторизации)."""
    job_config = GITLAB_JOBS.get(job_key)
    if not job_config:
        await send_message_with_reply_keyboard(
            f"❌ Неизвестная команда: {job_key}",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return

    env_emoji = "🧪" if env == "staging" else "🚀"
    joke = get_random_joke("deploy_start")

    await send_message_with_reply_keyboard(
        f"{joke}\n\n"
        f"<b>{env_emoji} Деплой {component} → {env.upper()}</b>\n\n"
        f"<i>⏳ Запускаю GitLab CI job...</i>",
        get_reply_keyboard(),
        chat_id=chat_id
    )

    # Триггерим job
    result = await trigger_gitlab_job(job_config["project"], job_config["job"])

    if result.get("success"):
        job_url = result.get("web_url", "")
        job_id = result.get("job_id")
        status = result.get("status", "pending")
        message = result.get("message", "")

        status_text = "⏳ Запущен" if status in ["pending", "running"] else f"📊 {status}"
        if message:
            status_text += f" ({message})"

        await send_message_with_reply_keyboard(
            f"✅ <b>Job запущен!</b>\n\n"
            f"<b>Компонент:</b> {component}\n"
            f"<b>Окружение:</b> {env_emoji} {env.upper()}\n"
            f"<b>Статус:</b> {status_text}\n"
            f"<b>Job ID:</b> #{job_id}\n\n"
            f"🔗 <a href=\"{job_url}\">Открыть в GitLab</a>\n\n"
            f"<i>Слежу за статусом...</i>",
            get_reply_keyboard(),
            chat_id=chat_id
        )

        # Запускаем мониторинг в фоне
        asyncio.create_task(monitor_deploy_job(chat_id, job_config["project"], job_id, component, env))
    else:
        error = result.get("error", "Unknown error")
        joke_error = get_random_joke("deploy_error")
        await send_message_with_reply_keyboard(
            f"{joke_error}\n\n"
            f"<b>❌ Не удалось запустить деплой</b>\n\n"
            f"<b>Ошибка:</b> {error}\n\n"
            f"<i>Попробуй позже или проверь GitLab</i>",
            get_reply_keyboard(),
            chat_id=chat_id
        )


async def monitor_deploy_job(chat_id: int, project: str, job_id: int, component: str, env: str):
    """Мониторит статус деплой job и отправляет уведомление по завершению."""
    max_wait = 600  # 10 минут максимум
    check_interval = 15
    elapsed = 0

    while elapsed < max_wait:
        await asyncio.sleep(check_interval)
        elapsed += check_interval

        result = await get_job_status(project, job_id)
        if not result.get("success"):
            continue

        status = result.get("status")

        if status == "success":
            joke = get_random_joke("deploy_success")
            duration = result.get("duration", 0)
            await send_message_with_reply_keyboard(
                f"{joke}\n\n"
                f"<b>✅ Деплой завершён успешно!</b>\n\n"
                f"<b>Компонент:</b> {component}\n"
                f"<b>Окружение:</b> {'🧪' if env == 'staging' else '🚀'} {env.upper()}\n"
                f"<b>Время:</b> {int(duration)}с\n\n"
                f"🔗 <a href=\"{result.get('web_url', '')}\">Подробности в GitLab</a>",
                get_reply_keyboard(),
                chat_id=chat_id
            )
            return

        elif status == "failed":
            joke = get_random_joke("deploy_error")
            await send_message_with_reply_keyboard(
                f"{joke}\n\n"
                f"<b>❌ Деплой провалился!</b>\n\n"
                f"<b>Компонент:</b> {component}\n"
                f"<b>Окружение:</b> {'🧪' if env == 'staging' else '🚀'} {env.upper()}\n\n"
                f"🔗 <a href=\"{result.get('web_url', '')}\">Смотри логи в GitLab</a>",
                get_reply_keyboard(),
                chat_id=chat_id
            )
            return

        elif status == "canceled":
            await send_message_with_reply_keyboard(
                f"⚠️ <b>Деплой отменён</b>\n\n"
                f"<b>Компонент:</b> {component}\n"
                f"<b>Окружение:</b> {env.upper()}",
                get_reply_keyboard(),
                chat_id=chat_id
            )
            return

    # Таймаут
    await send_message_with_reply_keyboard(
        f"⏱ <b>Деплой всё ещё выполняется...</b>\n\n"
        f"Прошло больше 10 минут. Проверь статус вручную в GitLab.",
        get_reply_keyboard(),
        chat_id=chat_id
    )
