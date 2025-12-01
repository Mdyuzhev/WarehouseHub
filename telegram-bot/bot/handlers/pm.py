"""
PM (Project Manager) функции.
Статус агента, аудит сторей, отчёты и прочая магия! 📊

Требования WH-88:
- Кнопка PM вместо Claude
- Статус агента (текущая работа Claude)
- Аудит открытых user stories
- Отчёты за день/неделю
"""

import asyncio
import httpx
import logging
from datetime import datetime
from bot.telegram import (
    send_message_with_reply_keyboard,
    send_message_with_inline_keyboard,
    send_message,
    send_chat_action
)
from bot.keyboards import get_reply_keyboard, get_pm_menu_keyboard
from bot.messages import get_random_joke
from services.youtrack import get_open_stories, get_activity_report, get_issue_by_id
from config import CLAUDE_PROXY_URL

logger = logging.getLogger(__name__)


async def handle_pm_menu(chat_id: int):
    """Показывает PM меню с inline кнопками."""
    joke = get_random_joke("pm_menu")

    msg = f"""
{joke}

<b>📊 PM Dashboard</b>

Выбери что тебя интересует:
• 🔄 <b>Сейчас в работе</b> — задачи In Progress
• 📋 <b>Аудит сторей</b> — открытые User Stories
• 📈 <b>Отчёт за день</b> — активность за сегодня
• 📅 <b>Отчёт за неделю</b> — активность за 7 дней
    """
    await send_message_with_inline_keyboard(
        msg.strip(),
        get_pm_menu_keyboard(),
        chat_id=chat_id
    )


async def handle_in_progress(chat_id: int):
    """Показывает последние выполненные задачи агентом."""
    from bot.handlers.claude import get_task_history

    await send_chat_action(chat_id, "typing")

    history = get_task_history(5)

    if not history:
        msg = """
🔄 <b>Сейчас в работе</b>

<i>Пока нет выполненных задач.</i>

Чтобы дать задачу агенту, используй команду 🤖 Claude.
        """
    else:
        msg = "🔄 <b>Последние задачи агента</b>\n\n"

        for i, item in enumerate(history, 1):
            task_text = item.get("task", "?")
            if len(task_text) > 60:
                task_text = task_text[:60] + "..."

            time_str = item.get("time", datetime.now()).strftime("%H:%M")
            duration = item.get("duration", 0)
            status = "✅" if item.get("success") else "❌"

            msg += f"{status} <b>{i}.</b> {task_text}\n"
            msg += f"   <i>⏱ {time_str} ({duration}с)</i>\n\n"

    await send_message_with_inline_keyboard(
        msg.strip(),
        get_pm_menu_keyboard(),
        chat_id=chat_id
    )


async def handle_stories_audit(chat_id: int):
    """Показывает аудит открытых User Stories."""
    await send_chat_action(chat_id, "typing")

    result = await get_open_stories()

    if not result.get("success"):
        msg = f"""
❌ <b>Ошибка загрузки сторей</b>

<i>{result.get('error', 'Неизвестная ошибка')}</i>
        """
        await send_message_with_inline_keyboard(msg.strip(), get_pm_menu_keyboard(), chat_id=chat_id)
        return

    stories = result.get("stories", [])
    count = result.get("count", 0)

    joke = get_random_joke("pm_audit")

    if count == 0:
        msg = f"""
{joke}

<b>📋 Аудит User Stories</b>

✨ <b>Все сделано!</b> Открытых сторей нет.

<i>Время пить кофе и придумывать новые фичи! ☕</i>
        """
    else:
        msg = f"""
{joke}

<b>📋 Аудит User Stories</b>
<i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>

📊 <b>Открытых сторей:</b> {count}

"""
        # Сортируем по приоритету
        priority_order = {"Critical": 0, "Major": 1, "Normal": 2, "Minor": 3}
        stories.sort(key=lambda x: priority_order.get(x.get("priority", "Normal"), 2))

        for story in stories[:10]:  # Ограничиваем 10 шт
            priority = story.get("priority", "Normal")
            priority_emoji = {
                "Critical": "🔴",
                "Major": "🟠",
                "Normal": "🟡",
                "Minor": "🟢"
            }.get(priority, "⚪")

            summary = story.get("summary", "No summary")
            if len(summary) > 50:
                summary = summary[:50] + "..."

            msg += f"{priority_emoji} <b>{story['id']}</b>: {summary}\n"

        if count > 10:
            msg += f"\n<i>...и ещё {count - 10} сторей</i>"

        msg += f"""

🔗 <a href="http://192.168.1.74:8088/issues/WH?q=State:Open%20Type:%7BUser%20Story%7D">Открыть в YouTrack</a>
        """

    await send_message_with_inline_keyboard(msg.strip(), get_pm_menu_keyboard(), chat_id=chat_id)


async def handle_daily_report(chat_id: int):
    """Показывает отчёт за сегодня."""
    await send_chat_action(chat_id, "typing")

    result = await get_activity_report(days=1)

    msg = format_activity_report(result, "день")

    await send_message_with_inline_keyboard(msg, get_pm_menu_keyboard(), chat_id=chat_id)


async def handle_weekly_report(chat_id: int):
    """Показывает отчёт за неделю."""
    await send_chat_action(chat_id, "typing")

    result = await get_activity_report(days=7)

    msg = format_activity_report(result, "неделю")

    await send_message_with_inline_keyboard(msg, get_pm_menu_keyboard(), chat_id=chat_id)


def format_activity_report(result: dict, period: str) -> str:
    """Форматирует отчёт по активности."""
    if not result.get("success"):
        return f"""
❌ <b>Ошибка загрузки отчёта</b>

<i>{result.get('error', 'Неизвестная ошибка')}</i>
        """

    completed = result.get("completed", [])
    in_progress = result.get("in_progress", [])
    started = result.get("started", [])
    silent = result.get("silent", [])

    joke = get_random_joke("pm_report")

    msg = f"""
{joke}

<b>📈 Отчёт за {period}</b>
<i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>

"""

    # Завершённые
    msg += f"✅ <b>Завершено:</b> {len(completed)}\n"
    for item in completed[:3]:
        msg += f"  • {item['id']}: {item.get('summary', '')[:40]}...\n"

    # В работе
    msg += f"\n🔄 <b>В работе:</b> {len(in_progress)}\n"
    for item in in_progress[:3]:
        msg += f"  • {item['id']}: {item.get('summary', '')[:40]}...\n"

    # Новые
    msg += f"\n🆕 <b>Начато:</b> {len(started)}\n"
    for item in started[:3]:
        msg += f"  • {item['id']}: {item.get('summary', '')[:40]}...\n"

    # Тишина (warning!)
    if silent:
        msg += f"\n⚠️ <b>Тишина (нет активности 3+ дней):</b> {len(silent)}\n"
        for item in silent[:3]:
            msg += f"  • {item['id']}: {item.get('summary', '')[:40]}...\n"
        msg += "\n<i>Эти задачи требуют внимания!</i>"

    # Вердикт
    if not in_progress and not silent:
        msg += "\n\n🎉 <b>Всё под контролем!</b>"
    elif silent:
        msg += "\n\n😬 <b>Есть задачи, которые застряли!</b>"
    else:
        msg += "\n\n💪 <b>Работа кипит!</b>"

    return msg.strip()


async def handle_issue_lookup(chat_id: int, issue_id: str):
    """Показывает информацию о конкретной задаче."""
    await send_chat_action(chat_id, "typing")

    result = await get_issue_by_id(issue_id)

    if not result.get("success"):
        msg = f"""
❌ <b>Задача не найдена</b>

<i>{issue_id}: {result.get('error', 'Неизвестная ошибка')}</i>
        """
        await send_message_with_reply_keyboard(msg.strip(), get_reply_keyboard(), chat_id=chat_id)
        return

    issue = result.get("issue", {})

    state_emoji = {
        "Open": "📋",
        "In Progress": "🔄",
        "In Review": "👀",
        "Done": "✅",
        "Verified": "✔️",
        "Closed": "🔒"
    }.get(issue.get("state", ""), "❓")

    priority_emoji = {
        "Critical": "🔴",
        "Major": "🟠",
        "Normal": "🟡",
        "Minor": "🟢"
    }.get(issue.get("priority", ""), "⚪")

    msg = f"""
<b>{issue.get('id', issue_id)}: {issue.get('summary', 'No summary')}</b>

{state_emoji} <b>Статус:</b> {issue.get('state', 'Unknown')}
{priority_emoji} <b>Приоритет:</b> {issue.get('priority', 'Normal')}
📦 <b>Тип:</b> {issue.get('type', 'Task')}
"""

    if issue.get("assignee"):
        msg += f"👤 <b>Исполнитель:</b> {issue['assignee']}\n"

    if issue.get("description"):
        desc = issue["description"][:300]
        if len(issue["description"]) > 300:
            desc += "..."
        msg += f"\n<b>Описание:</b>\n<i>{desc}</i>\n"

    msg += f"""
🔗 <a href="http://192.168.1.74:8088/issue/{issue.get('id', issue_id)}">Открыть в YouTrack</a>
    """

    await send_message_with_reply_keyboard(msg.strip(), get_reply_keyboard(), chat_id=chat_id)
