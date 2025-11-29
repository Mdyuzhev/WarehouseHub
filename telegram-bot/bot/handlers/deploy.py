"""
Обработчики команд деплоя.
Всё что связано с деплоем живёт здесь! 🚀
"""

import asyncio
from bot.telegram import send_message_with_reply_keyboard, send_message_with_inline_keyboard
from bot.keyboards import get_reply_keyboard, get_deploy_menu_keyboard
from bot.messages import get_random_joke
from services import trigger_gitlab_job, get_job_status
from config import GITLAB_JOBS


async def handle_deploy_menu(chat_id: int):
    """Показывает меню деплоя."""
    msg = """
<b>🚀 Меню деплоя</b>

Выбери что и куда деплоить:
    """
    await send_message_with_inline_keyboard(msg.strip(), get_deploy_menu_keyboard(), chat_id=chat_id)


async def handle_deploy_command(chat_id: int, job_key: str, component: str, env: str):
    """Запускает деплой через GitLab CI."""
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
