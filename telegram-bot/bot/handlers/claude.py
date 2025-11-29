"""
Claude AI интеграция.
Общаемся с Claude через бота! 🤖
"""

import asyncio
import httpx
from datetime import datetime
from bot.telegram import send_message_with_reply_keyboard, send_message
from bot.keyboards import get_reply_keyboard
from bot.messages import get_random_joke
from config import CLAUDE_PROXY_URL, LOAD_TEST_PASSWORD

# Состояние
pending_claude_task = {}
claude_task_status = {
    "running": False,
    "started_at": None,
    "chat_id": None,
    "task": None,
}


async def handle_claude_menu(chat_id: int):
    """Показывает меню Claude и запрашивает пароль."""
    global pending_claude_task

    if claude_task_status.get("running"):
        elapsed = datetime.now() - claude_task_status["started_at"]
        await send_message_with_reply_keyboard(
            f"⚠️ <b>Claude уже работает!</b>\n\n"
            f"⏱ Время: {int(elapsed.total_seconds())}с\n"
            f"<i>Дождись завершения текущей задачи.</i>",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return

    pending_claude_task[chat_id] = {"step": "password"}

    msg = """
<b>🤖 Claude AI Assistant</b>

Здесь можно отправить задачу напрямую Claude Code.
Он выполнит её и вернёт результат.

<b>🔐 Введи пароль для доступа:</b>

<i>⏱ У тебя 60 секунд...</i>
    """
    await send_message(msg.strip(), chat_id=chat_id)

    asyncio.create_task(clear_pending_claude(chat_id, 60))


async def clear_pending_claude(chat_id: int, seconds: int):
    """Очищает ожидание Claude ввода."""
    await asyncio.sleep(seconds)
    if chat_id in pending_claude_task:
        del pending_claude_task[chat_id]
        await send_message_with_reply_keyboard(
            "⏱ <b>Время вышло!</b>\n\nЗапрос на Claude отменён.",
            get_reply_keyboard(),
            chat_id=chat_id
        )


async def handle_claude_input(chat_id: int, text: str) -> bool:
    """Обрабатывает ввод пароля или задачи для Claude."""
    global pending_claude_task

    if chat_id not in pending_claude_task:
        return False

    state = pending_claude_task[chat_id]
    step = state.get("step")

    if step == "password":
        if text == LOAD_TEST_PASSWORD:
            pending_claude_task[chat_id] = {"step": "task"}
            await send_message(
                "✅ <b>Пароль принят!</b>\n\n"
                "📝 <b>Введи задачу для Claude:</b>\n\n"
                "<i>Например: \"Проверь статус всех сервисов в K8s\"</i>",
                chat_id=chat_id
            )
        else:
            del pending_claude_task[chat_id]
            await send_message_with_reply_keyboard(
                "❌ <b>Неверный пароль!</b>\n\n<i>Доступ к Claude запрещён.</i>",
                get_reply_keyboard(),
                chat_id=chat_id
            )
        return True

    elif step == "task":
        del pending_claude_task[chat_id]

        task = text.strip()
        if len(task) < 3:
            await send_message_with_reply_keyboard(
                "⚠️ <b>Задача слишком короткая!</b>\n\n<i>Попробуй ещё раз через меню Claude.</i>",
                get_reply_keyboard(),
                chat_id=chat_id
            )
            return True

        await execute_claude_task(chat_id, task)
        return True

    return False


async def execute_claude_task(chat_id: int, task: str):
    """Выполняет задачу через Claude Proxy API."""
    global claude_task_status

    joke = get_random_joke("claude_start")

    await send_message_with_reply_keyboard(
        f"{joke}\n\n"
        f"<b>📝 Задача:</b>\n<code>{task[:200]}{'...' if len(task) > 200 else ''}</code>\n\n"
        f"<i>⏳ Ожидай ответ... (до 5 мин)</i>",
        get_reply_keyboard(),
        chat_id=chat_id
    )

    claude_task_status = {
        "running": True,
        "started_at": datetime.now(),
        "chat_id": chat_id,
        "task": task,
    }

    try:
        async with httpx.AsyncClient(timeout=310.0) as client:
            response = await client.post(
                f"{CLAUDE_PROXY_URL}/execute",
                json={
                    "task": task,
                    "cwd": "/home/flomaster/warehouse-api",
                    "timeout": 300
                }
            )

            elapsed = datetime.now() - claude_task_status["started_at"]
            elapsed_sec = int(elapsed.total_seconds())

            if response.status_code == 200:
                data = response.json()

                if data.get("success"):
                    result = data.get("stdout", "").strip()
                    joke_done = get_random_joke("claude_done")

                    if len(result) > 3500:
                        result = result[:3500] + "\n\n<i>... (обрезано)</i>"

                    # Экранируем HTML
                    result = result.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                    await send_message_with_reply_keyboard(
                        f"{joke_done}\n\n"
                        f"<b>🤖 Ответ Claude:</b>\n\n"
                        f"<pre>{result}</pre>\n\n"
                        f"<i>⏱ Время: {elapsed_sec}с</i>",
                        get_reply_keyboard(),
                        chat_id=chat_id
                    )
                else:
                    error = data.get("stderr", "Неизвестная ошибка")
                    joke_error = get_random_joke("claude_error")
                    error = error.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                    await send_message_with_reply_keyboard(
                        f"{joke_error}\n\n"
                        f"<b>❌ Ошибка выполнения</b>\n\n"
                        f"<pre>{error[:500]}</pre>",
                        get_reply_keyboard(),
                        chat_id=chat_id
                    )
            else:
                joke_error = get_random_joke("claude_error")
                await send_message_with_reply_keyboard(
                    f"{joke_error}\n\n"
                    f"<b>❌ Ошибка API</b>\n\n"
                    f"HTTP {response.status_code}",
                    get_reply_keyboard(),
                    chat_id=chat_id
                )

    except Exception as e:
        joke_error = get_random_joke("claude_error")
        await send_message_with_reply_keyboard(
            f"{joke_error}\n\n"
            f"<b>❌ Ошибка соединения</b>\n\n"
            f"<i>{str(e)[:100]}</i>",
            get_reply_keyboard(),
            chat_id=chat_id
        )

    finally:
        claude_task_status = {
            "running": False,
            "started_at": None,
            "chat_id": None,
            "task": None,
        }


def is_pending_claude(chat_id: int) -> bool:
    """Проверяет, ожидается ли ввод для Claude."""
    return chat_id in pending_claude_task
