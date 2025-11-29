# План реализации PM-функций для Telegram бота

**Дата:** 29 ноября 2025
**Автор:** Claude Code
**Связанная стора:** TBD (создадим в YouTrack)

---

## Обзор изменений

Превращаем кнопку "Claude" в "PM" (Project Manager) с функциями:
1. Статус текущей работы агента
2. Аудит по открытым user stories
3. Отчёты за день/неделю

Плюс улучшаем уведомления GitLab и добавляем юмор.

---

## Часть 1: Кнопка PM и её меню

### 1.1 Изменения в `keyboards.py`

**Файл:** `telegram-bot/bot/keyboards.py`

```python
# Было:
[{"text": "🤖 Claude"}, {"text": "🎰 Шутка"}, {"text": "❓"}]

# Станет:
[{"text": "📋 PM"}, {"text": "🎰 Шутка"}, {"text": "❓"}]
```

**Новые клавиатуры:**

```python
def get_pm_menu_keyboard() -> dict:
    """Меню Project Manager."""
    return {
        "inline_keyboard": [
            [{"text": "📊 Статус агента", "callback_data": "pm_status"}],
            [{"text": "📋 Аудит сторей", "callback_data": "pm_audit"}],
            [{"text": "📝 Отчёт", "callback_data": "pm_report"}],
            [{"text": "⬅️ Назад", "callback_data": "menu"}],
        ]
    }

def get_report_period_keyboard() -> dict:
    """Выбор периода отчёта."""
    return {
        "inline_keyboard": [
            [{"text": "📅 За сегодня", "callback_data": "pm_report_day"}],
            [{"text": "📆 За неделю", "callback_data": "pm_report_week"}],
            [{"text": "⬅️ Назад", "callback_data": "pm_menu"}],
        ]
    }

def get_stories_keyboard(stories: list, page: int = 0) -> dict:
    """Список открытых сторей с пагинацией (по 5 штук)."""
    PAGE_SIZE = 5
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_stories = stories[start:end]

    buttons = []
    for story in page_stories:
        # story = {"id": "WH-65", "summary": "Инфраструктура..."}
        short_summary = story["summary"][:30] + "..." if len(story["summary"]) > 30 else story["summary"]
        buttons.append([{
            "text": f"📌 {story['id']}: {short_summary}",
            "callback_data": f"pm_story_{story['id']}"
        }])

    # Навигация
    nav = []
    if page > 0:
        nav.append({"text": "⬅️", "callback_data": f"pm_audit_page_{page-1}"})
    if end < len(stories):
        nav.append({"text": "➡️", "callback_data": f"pm_audit_page_{page+1}"})
    if nav:
        buttons.append(nav)

    buttons.append([{"text": "⬅️ Назад", "callback_data": "pm_menu"}])

    return {"inline_keyboard": buttons}
```

---

### 1.2 Новый handler `pm.py`

**Файл:** `telegram-bot/bot/handlers/pm.py` (новый)

```python
"""
Project Manager функции.
Статусы, аудиты, отчёты - всё для босса! 📋
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from bot.telegram import send_message, send_message_with_inline_keyboard
from bot.keyboards import (
    get_pm_menu_keyboard,
    get_report_period_keyboard,
    get_stories_keyboard
)
from bot.messages import get_random_joke
from config import CLAUDE_PROXY_URL, YOUTRACK_URL, YOUTRACK_TOKEN
from services.youtrack import (
    get_open_stories,
    get_story_details,
    get_tasks_for_period
)

# Кэш для пагинации
stories_cache = {}


async def handle_pm_menu(chat_id: int):
    """Показывает PM меню."""
    msg = """
<b>📋 Project Manager</b>

Выбери действие:

📊 <b>Статус агента</b> - текущая работа Claude
📋 <b>Аудит сторей</b> - проверка открытых историй
📝 <b>Отчёт</b> - сводка за день/неделю
    """
    await send_message_with_inline_keyboard(
        msg.strip(),
        get_pm_menu_keyboard(),
        chat_id=chat_id
    )


async def handle_pm_status(chat_id: int):
    """Запрашивает статус у Claude proxy."""
    await send_message("⏳ Запрашиваю статус агента...", chat_id=chat_id)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{CLAUDE_PROXY_URL}/status")

            if response.status_code == 200:
                data = response.json()
                msg = format_agent_status(data)
            else:
                msg = "❌ Не удалось получить статус агента"

    except Exception as e:
        msg = f"❌ Ошибка соединения: {str(e)[:100]}"

    await send_message_with_inline_keyboard(
        msg,
        get_pm_menu_keyboard(),
        chat_id=chat_id
    )


def format_agent_status(data: dict) -> str:
    """Форматирует статус агента в красивое сообщение."""
    if not data.get("active"):
        return """
<b>📊 Статус агента</b>

🟢 <b>Состояние:</b> Свободен
<i>Агент готов к новым задачам</i>
        """.strip()

    task = data.get("task", "Не указана")
    current = data.get("current_action", "В процессе...")
    progress = data.get("progress", "")
    started = data.get("started_at", "")

    # Считаем время работы
    elapsed = ""
    if started:
        try:
            start_time = datetime.fromisoformat(started)
            delta = datetime.now() - start_time
            elapsed = f"⏱ Работает: {int(delta.total_seconds() // 60)}м {int(delta.total_seconds() % 60)}с"
        except:
            pass

    return f"""
<b>📊 Статус агента</b>

🔵 <b>Состояние:</b> Работает

📌 <b>Задача:</b> {task}
🔧 <b>Сейчас:</b> {current}
📈 <b>Прогресс:</b> {progress}
{elapsed}
    """.strip()


async def handle_pm_audit(chat_id: int, page: int = 0):
    """Показывает список открытых user stories."""
    await send_message("⏳ Загружаю открытые стори...", chat_id=chat_id)

    try:
        stories = await get_open_stories()

        if not stories:
            await send_message_with_inline_keyboard(
                "✅ <b>Все стори закрыты!</b>\n\n<i>Нет открытых user stories в проекте.</i>",
                get_pm_menu_keyboard(),
                chat_id=chat_id
            )
            return

        # Кэшируем для пагинации
        stories_cache[chat_id] = stories

        msg = f"""
<b>📋 Открытые User Stories</b>

Найдено: <b>{len(stories)}</b> шт.

<i>Выбери сторю для детального отчёта:</i>
        """

        await send_message_with_inline_keyboard(
            msg.strip(),
            get_stories_keyboard(stories, page),
            chat_id=chat_id
        )

    except Exception as e:
        await send_message_with_inline_keyboard(
            f"❌ Ошибка загрузки: {str(e)[:100]}",
            get_pm_menu_keyboard(),
            chat_id=chat_id
        )


async def handle_story_details(chat_id: int, story_id: str):
    """Показывает детали конкретной стори с подзадачами."""
    await send_message(f"⏳ Загружаю детали {story_id}...", chat_id=chat_id)

    try:
        details = await get_story_details(story_id)
        msg = format_story_details(details)

        await send_message_with_inline_keyboard(
            msg,
            get_pm_menu_keyboard(),
            chat_id=chat_id
        )

    except Exception as e:
        await send_message_with_inline_keyboard(
            f"❌ Ошибка: {str(e)[:100]}",
            get_pm_menu_keyboard(),
            chat_id=chat_id
        )


def format_story_details(details: dict) -> str:
    """Форматирует детали стори."""
    story = details.get("story", {})
    tasks = details.get("tasks", [])

    # Группируем задачи по статусу
    done = [t for t in tasks if t["status"] in ["Done", "Closed", "Verified"]]
    in_progress = [t for t in tasks if t["status"] == "In Progress"]
    todo = [t for t in tasks if t["status"] in ["Open", "To Do"]]

    msg = f"""
<b>📌 {story.get('id', 'N/A')}: {story.get('summary', 'Без названия')}</b>

📊 <b>Прогресс:</b> {len(done)}/{len(tasks)} задач

<b>━━━ ✅ Выполнено ({len(done)}) ━━━</b>
"""

    for t in done[:5]:  # Макс 5 для краткости
        msg += f"• <a href='{t['url']}'>{t['id']}</a>: {t['summary'][:40]}\n"
    if len(done) > 5:
        msg += f"<i>... и ещё {len(done) - 5}</i>\n"

    msg += f"\n<b>━━━ 🔄 В работе ({len(in_progress)}) ━━━</b>\n"
    for t in in_progress:
        msg += f"• <a href='{t['url']}'>{t['id']}</a>: {t['summary'][:40]}\n"
    if not in_progress:
        msg += "<i>Нет задач в работе</i>\n"

    msg += f"\n<b>━━━ ⏳ Ожидает ({len(todo)}) ━━━</b>\n"
    for t in todo[:5]:
        msg += f"• <a href='{t['url']}'>{t['id']}</a>: {t['summary'][:40]}\n"
    if len(todo) > 5:
        msg += f"<i>... и ещё {len(todo) - 5}</i>\n"
    if not todo:
        msg += "<i>Все задачи в работе или завершены</i>\n"

    # Ссылка на сторю
    msg += f"\n🔗 <a href='{story.get('url', '')}'>Открыть в YouTrack</a>"

    return msg.strip()


async def handle_pm_report(chat_id: int):
    """Показывает меню выбора периода отчёта."""
    msg = """
<b>📝 Отчёт по задачам</b>

Выбери период:

📅 <b>За сегодня</b> - активность за текущий день
📆 <b>За неделю</b> - сводка за 7 дней
    """
    await send_message_with_inline_keyboard(
        msg.strip(),
        get_report_period_keyboard(),
        chat_id=chat_id
    )


async def handle_report_generate(chat_id: int, period: str):
    """Генерирует отчёт за указанный период."""
    period_name = "сегодня" if period == "day" else "неделю"
    await send_message(f"⏳ Генерирую отчёт за {period_name}...", chat_id=chat_id)

    try:
        # Определяем даты
        now = datetime.now()
        if period == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            silence_threshold = 0  # Любые открытые без активности за день
        else:  # week
            start_date = now - timedelta(days=7)
            silence_threshold = 3  # Молчат 3+ дня

        data = await get_tasks_for_period(start_date, now, silence_threshold)
        msg = format_period_report(data, period)

        await send_message_with_inline_keyboard(
            msg,
            get_pm_menu_keyboard(),
            chat_id=chat_id
        )

    except Exception as e:
        await send_message_with_inline_keyboard(
            f"❌ Ошибка генерации: {str(e)[:100]}",
            get_pm_menu_keyboard(),
            chat_id=chat_id
        )


def format_period_report(data: dict, period: str) -> str:
    """Форматирует отчёт за период."""
    completed = data.get("completed", [])
    in_progress = data.get("in_progress", [])
    started = data.get("started", [])
    silent = data.get("silent", [])

    period_name = "сегодня" if period == "day" else "неделю"
    period_emoji = "📅" if period == "day" else "📆"

    msg = f"""
<b>{period_emoji} Отчёт за {period_name}</b>
<i>{datetime.now().strftime('%d.%m.%Y %H:%M')}</i>

<b>━━━ ✅ Завершено ({len(completed)}) ━━━</b>
"""

    for t in completed[:7]:
        msg += f"• <a href='{t['url']}'>{t['id']}</a>: {t['summary'][:35]}\n"
    if len(completed) > 7:
        msg += f"<i>... и ещё {len(completed) - 7}</i>\n"
    if not completed:
        msg += "<i>Нет завершённых задач</i>\n"

    msg += f"\n<b>━━━ 🔄 В работе ({len(in_progress)}) ━━━</b>\n"
    for t in in_progress[:5]:
        msg += f"• <a href='{t['url']}'>{t['id']}</a>: {t['summary'][:35]}\n"
    if not in_progress:
        msg += "<i>Нет задач в работе</i>\n"

    msg += f"\n<b>━━━ 🆕 Начато ({len(started)}) ━━━</b>\n"
    for t in started[:5]:
        msg += f"• <a href='{t['url']}'>{t['id']}</a>: {t['summary'][:35]}\n"
    if not started:
        msg += "<i>Новых задач не начато</i>\n"

    # Тишина
    if silent:
        silence_days = "сегодня" if period == "day" else "3+ дней"
        msg += f"\n<b>━━━ 🔇 Тишина - нет активности {silence_days} ({len(silent)}) ━━━</b>\n"
        for t in silent[:5]:
            days = t.get('silent_days', '?')
            msg += f"• <a href='{t['url']}'>{t['id']}</a>: {t['summary'][:30]} <i>(молчит {days}д)</i>\n"
        if len(silent) > 5:
            msg += f"<i>... и ещё {len(silent) - 5}</i>\n"

    # Сводка
    total_active = len(completed) + len(in_progress) + len(started)
    msg += f"\n📊 <b>Итого активность:</b> {total_active} задач"
    if silent:
        msg += f"\n⚠️ <b>Требуют внимания:</b> {len(silent)} задач"

    return msg.strip()
```

---

### 1.3 Новый сервис `youtrack.py`

**Файл:** `telegram-bot/services/youtrack.py` (новый)

```python
"""
YouTrack API интеграция.
Работаем с задачами и сторями! 📋
"""

import httpx
from datetime import datetime
from typing import List, Dict, Optional
from config import YOUTRACK_URL, YOUTRACK_TOKEN, YOUTRACK_PROJECT

# YouTrack API Headers
HEADERS = {
    "Authorization": f"Bearer {YOUTRACK_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}


async def get_open_stories() -> List[Dict]:
    """
    Получает список открытых User Stories.

    Returns:
        List[Dict]: [{"id": "WH-65", "summary": "...", "url": "..."}]
    """
    query = f"project: {YOUTRACK_PROJECT} Type: {{User Story}} State: -Closed -Done"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{YOUTRACK_URL}/api/issues",
            headers=HEADERS,
            params={
                "query": query,
                "fields": "idReadable,summary,resolved",
                "$top": 50
            }
        )
        response.raise_for_status()

        issues = response.json()
        return [
            {
                "id": issue["idReadable"],
                "summary": issue["summary"],
                "url": f"{YOUTRACK_URL}/issue/{issue['idReadable']}"
            }
            for issue in issues
        ]


async def get_story_details(story_id: str) -> Dict:
    """
    Получает детали стори и её подзадачи.

    Args:
        story_id: ID стори (например, "WH-65")

    Returns:
        Dict: {"story": {...}, "tasks": [...]}
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Получаем сторю
        response = await client.get(
            f"{YOUTRACK_URL}/api/issues/{story_id}",
            headers=HEADERS,
            params={
                "fields": "idReadable,summary,description,resolved,customFields(name,value(name))"
            }
        )
        response.raise_for_status()
        story_data = response.json()

        # Парсим статус
        status = "Open"
        for field in story_data.get("customFields", []):
            if field.get("name") == "State":
                value = field.get("value")
                if value:
                    status = value.get("name", "Open")
                break

        story = {
            "id": story_data["idReadable"],
            "summary": story_data["summary"],
            "status": status,
            "url": f"{YOUTRACK_URL}/issue/{story_data['idReadable']}"
        }

        # Получаем подзадачи (subtasks/links)
        tasks = await get_subtasks(story_id)

        return {"story": story, "tasks": tasks}


async def get_subtasks(parent_id: str) -> List[Dict]:
    """Получает подзадачи для стори."""
    query = f"project: {YOUTRACK_PROJECT} parent: {parent_id}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{YOUTRACK_URL}/api/issues",
            headers=HEADERS,
            params={
                "query": query,
                "fields": "idReadable,summary,resolved,customFields(name,value(name))",
                "$top": 100
            }
        )
        response.raise_for_status()

        issues = response.json()
        tasks = []

        for issue in issues:
            status = "Open"
            for field in issue.get("customFields", []):
                if field.get("name") == "State":
                    value = field.get("value")
                    if value:
                        status = value.get("name", "Open")
                    break

            tasks.append({
                "id": issue["idReadable"],
                "summary": issue["summary"],
                "status": status,
                "url": f"{YOUTRACK_URL}/issue/{issue['idReadable']}"
            })

        return tasks


async def get_tasks_for_period(
    start_date: datetime,
    end_date: datetime,
    silence_threshold_days: int = 3
) -> Dict:
    """
    Получает задачи с активностью за период.

    Args:
        start_date: Начало периода
        end_date: Конец периода
        silence_threshold_days: Порог "тишины" в днях

    Returns:
        Dict: {
            "completed": [...],
            "in_progress": [...],
            "started": [...],
            "silent": [...]
        }
    """
    start_ts = int(start_date.timestamp() * 1000)
    end_ts = int(end_date.timestamp() * 1000)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Завершённые за период
        completed_query = f"project: {YOUTRACK_PROJECT} resolved: {start_ts} .. {end_ts}"
        completed_resp = await client.get(
            f"{YOUTRACK_URL}/api/issues",
            headers=HEADERS,
            params={
                "query": completed_query,
                "fields": "idReadable,summary,resolved",
                "$top": 100
            }
        )
        completed = parse_issues(completed_resp.json()) if completed_resp.status_code == 200 else []

        # В работе сейчас
        in_progress_query = f"project: {YOUTRACK_PROJECT} State: {{In Progress}}"
        in_progress_resp = await client.get(
            f"{YOUTRACK_URL}/api/issues",
            headers=HEADERS,
            params={
                "query": in_progress_query,
                "fields": "idReadable,summary,updated",
                "$top": 50
            }
        )
        in_progress = parse_issues(in_progress_resp.json()) if in_progress_resp.status_code == 200 else []

        # Начатые за период (перешли в In Progress)
        # Это сложнее - нужна история изменений, упрощаем: созданные за период
        started_query = f"project: {YOUTRACK_PROJECT} created: {start_ts} .. {end_ts}"
        started_resp = await client.get(
            f"{YOUTRACK_URL}/api/issues",
            headers=HEADERS,
            params={
                "query": started_query,
                "fields": "idReadable,summary,created",
                "$top": 50
            }
        )
        started = parse_issues(started_resp.json()) if started_resp.status_code == 200 else []

        # Тишина - открытые без обновлений
        silence_ts = int((end_date - timedelta(days=silence_threshold_days)).timestamp() * 1000)
        silent_query = f"project: {YOUTRACK_PROJECT} State: -Closed -Done updated: -.. {silence_ts}"
        silent_resp = await client.get(
            f"{YOUTRACK_URL}/api/issues",
            headers=HEADERS,
            params={
                "query": silent_query,
                "fields": "idReadable,summary,updated",
                "$top": 50
            }
        )
        silent_issues = silent_resp.json() if silent_resp.status_code == 200 else []

        # Добавляем дни тишины
        silent = []
        for issue in silent_issues:
            updated = issue.get("updated", 0)
            if updated:
                days_silent = (end_date - datetime.fromtimestamp(updated / 1000)).days
            else:
                days_silent = "?"

            silent.append({
                "id": issue["idReadable"],
                "summary": issue["summary"],
                "silent_days": days_silent,
                "url": f"{YOUTRACK_URL}/issue/{issue['idReadable']}"
            })

        return {
            "completed": completed,
            "in_progress": in_progress,
            "started": started,
            "silent": silent
        }


def parse_issues(issues: list) -> List[Dict]:
    """Парсит список issues в простой формат."""
    return [
        {
            "id": issue["idReadable"],
            "summary": issue["summary"],
            "url": f"{YOUTRACK_URL}/issue/{issue['idReadable']}"
        }
        for issue in issues
    ]
```

---

### 1.4 Обновление `config.py`

**Добавить:**

```python
# =============================================================================
# YouTrack
# =============================================================================
YOUTRACK_URL = os.getenv("YOUTRACK_URL", "http://192.168.1.74:8088")
YOUTRACK_TOKEN = os.getenv("YOUTRACK_TOKEN", "perm:xxx")  # Permanent token
YOUTRACK_PROJECT = os.getenv("YOUTRACK_PROJECT", "WH")
```

---

### 1.5 Обновление `app.py`

**Добавить обработку callback'ов:**

```python
# В process_callback():

elif callback_data == "pm_menu":
    await handle_pm_menu(chat_id)

elif callback_data == "pm_status":
    await handle_pm_status(chat_id)

elif callback_data == "pm_audit":
    await handle_pm_audit(chat_id)

elif callback_data.startswith("pm_audit_page_"):
    page = int(callback_data.split("_")[-1])
    await handle_pm_audit(chat_id, page)

elif callback_data.startswith("pm_story_"):
    story_id = callback_data.replace("pm_story_", "")
    await handle_story_details(chat_id, story_id)

elif callback_data == "pm_report":
    await handle_pm_report(chat_id)

elif callback_data == "pm_report_day":
    await handle_report_generate(chat_id, "day")

elif callback_data == "pm_report_week":
    await handle_report_generate(chat_id, "week")
```

**Обновить обработку кнопок:**

```python
# Было:
elif text in ["🤖 Claude", "claude"]:
    await handle_claude_menu(chat_id)

# Станет:
elif text in ["📋 PM", "pm"]:
    await handle_pm_menu(chat_id)
```

---

### 1.6 Сохраняем код Claude (закомментируем)

**Файл:** `telegram-bot/bot/handlers/claude.py`

Оставляем файл как есть, но в `app.py` комментируем обработку.
Добавляем в начало файла:

```python
"""
⚠️ DEPRECATED: Claude AI интеграция временно отключена.
Код сохранён для возможного использования в будущем.
Заменено на PM-функции (см. pm.py)
"""
```

---

## Часть 2: Улучшенные GitLab уведомления

### 2.1 Парсинг задачи из ветки/коммита

**Файл:** `telegram-bot/bot/messages.py`

**Добавить функцию:**

```python
import re

def extract_task_id(branch: str, commit_message: str = "") -> Optional[str]:
    """
    Извлекает ID задачи YouTrack из ветки или коммита.

    Приоритет: ветка > коммит
    Паттерны: WH-123, feature/WH-123-description, fix(WH-123): message
    """
    patterns = [
        r'(WH-\d+)',           # WH-123
        r'feature/(WH-\d+)',   # feature/WH-123-xxx
        r'fix/(WH-\d+)',       # fix/WH-123-xxx
        r'bugfix/(WH-\d+)',    # bugfix/WH-123-xxx
        r'\((WH-\d+)\)',       # feat(WH-123): xxx
    ]

    # Сначала ищем в ветке
    for pattern in patterns:
        match = re.search(pattern, branch, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    # Потом в коммите
    for pattern in patterns:
        match = re.search(pattern, commit_message, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    return None
```

### 2.2 Маппинг stages

**Файл:** `telegram-bot/bot/messages.py`

**Добавить:**

```python
STAGE_INFO = {
    "build": {
        "name": "Сборка",
        "description": "компилируем код",
        "order": 1
    },
    "test": {
        "name": "Тестирование",
        "description": "проверяем что работает",
        "order": 2
    },
    "lint": {
        "name": "Линтинг",
        "description": "проверяем стиль кода",
        "order": 2
    },
    "security": {
        "name": "Безопасность",
        "description": "сканируем на уязвимости",
        "order": 3
    },
    "package": {
        "name": "Упаковка",
        "description": "собираем Docker образ",
        "order": 4
    },
    "deploy-staging": {
        "name": "Деплой STAGING",
        "description": "катим на тестовый сервер",
        "order": 5
    },
    "deploy-prod": {
        "name": "Деплой PROD",
        "description": "катим в бой!",
        "order": 6
    },
    "deploy": {
        "name": "Деплой",
        "description": "катим на сервер",
        "order": 5
    },
}

def get_stage_info(stage: str, total_stages: int = None) -> str:
    """
    Возвращает информацию о stage.

    Args:
        stage: Название stage (build, test, etc.)
        total_stages: Общее количество stages в pipeline

    Returns:
        str: "Этап 2/4: Тестирование - проверяем что работает"
    """
    info = STAGE_INFO.get(stage.lower(), {
        "name": stage.capitalize(),
        "description": "выполняем работу",
        "order": 0
    })

    if total_stages and info["order"]:
        return f"Этап {info['order']}/{total_stages}: {info['name']} - {info['description']}"
    else:
        return f"{info['name']} - {info['description']}"
```

### 2.3 Обновление формата сообщений

**Файл:** `telegram-bot/bot/messages.py`

**Обновить `format_job_message`:**

```python
def format_job_message(data: dict) -> str:
    """Форматирует сообщение о job событии с информацией о задаче."""
    status = data.get("build_status", "unknown")
    emoji = get_status_emoji(status)

    project = data.get("project_name", "Unknown")
    ref = data.get("ref", "unknown")
    job_name = data.get("build_name", "unknown-job")
    job_id = data.get("build_id", "?")
    stage = data.get("build_stage", "?")
    commit_msg = data.get("commit", {}).get("message", "") if isinstance(data.get("commit"), dict) else ""
    username = data.get("user", {}).get("name", "Ghost") if isinstance(data.get("user"), dict) else "Ghost"

    # Извлекаем задачу
    task_id = extract_task_id(ref, commit_msg)
    task_line = f"📌 <b>Задача:</b> <a href='http://192.168.1.74:8088/issue/{task_id}'>{task_id}</a>\n" if task_id else ""

    # Информация о stage
    stage_info = get_stage_info(stage)

    # Длительность
    duration = data.get("build_duration")
    duration_str = ""
    if duration:
        minutes = int(duration) // 60
        seconds = int(duration) % 60
        duration_str = f"\n⏱ Время: {minutes}м {seconds}с"

    # Что ожидаем в конце
    expectation = get_stage_expectation(stage, status)

    humor = get_humor_for_status(status, "job")

    if status == "running":
        msg = f"""
{emoji} <b>Job Started: {job_name}</b>

{task_line}📦 <b>Проект:</b> {project}
🌿 <b>Ветка:</b> {ref}
🏗 <b>{stage_info}</b>
🆔 <b>Job ID:</b> #{job_id}
👤 <b>Автор:</b> {username}

{expectation}

{humor}
"""
    else:
        msg = f"""
{emoji} <b>Job {status.upper()}: {job_name}</b>

{task_line}📦 <b>Проект:</b> {project}
🌿 <b>Ветка:</b> {ref}
🏗 <b>{stage_info}</b>
🆔 <b>Job ID:</b> #{job_id}
👤 <b>Автор:</b> {username}{duration_str}

{humor}
"""

    return msg.strip()


def get_stage_expectation(stage: str, status: str) -> str:
    """Возвращает что ожидаем в конце этапа."""
    if status != "running":
        return ""

    expectations = {
        "build": "🎯 Ожидаем: успешная компиляция без ошибок",
        "test": "🎯 Ожидаем: все тесты зелёные",
        "lint": "🎯 Ожидаем: код соответствует стандартам",
        "security": "🎯 Ожидаем: нет критических уязвимостей",
        "package": "🎯 Ожидаем: Docker образ готов",
        "deploy-staging": "🎯 Ожидаем: приложение доступно на staging",
        "deploy-prod": "🎯 Ожидаем: приложение обновлено на проде",
        "deploy": "🎯 Ожидаем: успешный деплой",
    }

    return expectations.get(stage.lower(), "🎯 Ожидаем: успешное завершение")
```

---

## Часть 3: Больше юмора

### 3.1 Расширяем `JOKES` в `messages.py`

```python
JOKES = {
    # ... существующие категории ...

    "pipeline_success": [
        "Ура! Всё взлетело! 🎉",
        "Зелёненькое! Чудеса случаются! ✨",
        "Работает! Даже странно... 🤔",
        "Успех! Иди налей себе кофе, заслужил! ☕",
        "Pipeline прошёл! Кто не верил - покайтесь! 🙏",
        "Всё зелёное! Либо код хороший, либо тестов мало 😏",
        "Успех! Сегодня можно спать спокойно... наверное 😴",
        "It works! На моей машине и на CI тоже! 🎰",
    ],

    "pipeline_failed": [
        "Упс... Кто-то накосячил! 🙈",
        "ПРОВАЛ! Время смотреть логи... 📜",
        "Красненькое! Классика пятничного деплоя! 🔥",
        "Failed! Но мы не сдаёмся, правда? 💪",
        "Ну, бывает. Кто не падал - тот не деплоил 🤷",
        "Красный билд - к деньгам! Или к овертайму... 💸",
        "F. Респект не нажимаем. 😔",
        "Houston, we have a problem! 🚀💥",
    ],

    "pipeline_running": [
        "Поехали! Держитесь! 🚀",
        "Крутим, мутим... ⚙️",
        "В процессе... Пойду кофе попью. ☕",
        "Работаем-работаем! 🔧",
        "Пошёл варить кофе? Правильное решение! ☕",
        "Ждём-с... Можно пока мемы посмотреть 📱",
        "CI работает, а ты чем занят? 🤨",
    ],

    "deploy_prod": [
        "Поехали на прод! Крестимся и деплоим 🙏",
        "Deploy to PROD! Надеюсь, ты знаешь что делаешь 😱",
        "Катим в бой! Держитесь, юзеры! 🎢",
        "PROD deploy! Это не drill! 🚨",
        "Продакшн? В пятницу? Ты смелый! 🦁",
    ],

    "pm_status_free": [
        "Агент отдыхает... Редкое зрелище! 🏖",
        "Claude свободен! Можно нагрузить работой 💪",
        "Тишина... Подозрительная тишина... 🤫",
    ],

    "pm_status_busy": [
        "Работаем! Кофе не предлагать! 💻",
        "В процессе... Не отвлекать! 🔧",
        "Claude занят. Очень занят. Оооочень занят. 🏃",
    ],

    "report_good": [
        "Продуктивный был день! 📈",
        "Много сделано! Так держать! 💪",
        "Красота! Работа кипит! 🔥",
    ],

    "report_silent": [
        "Тут тишина... Тревожная тишина... 🔇",
        "Эти задачи заскучали без внимания 😢",
        "Кто-то забыл про эти таски... 👀",
    ],
}
```

---

## Часть 4: Claude Proxy - эндпоинт /status

### 4.1 Добавить эндпоинт в Claude Proxy

**Файл:** (где-то в claude-proxy, надо уточнить структуру)

```python
@app.get("/status")
async def get_status():
    """Возвращает текущий статус агента."""
    global current_task

    if not current_task or not current_task.get("active"):
        return {"active": False}

    return {
        "active": True,
        "task": current_task.get("task", ""),
        "current_action": current_task.get("current_action", "В процессе..."),
        "progress": current_task.get("progress", ""),
        "started_at": current_task.get("started_at", "")
    }
```

*Нужно будет уточнить структуру claude-proxy для точной реализации.*

---

## Часть 5: Интеграция и тестирование

### 5.1 Файлы для изменения

| Файл | Действие |
|------|----------|
| `telegram-bot/config.py` | Добавить YOUTRACK_* константы |
| `telegram-bot/bot/keyboards.py` | Добавить PM клавиатуры, заменить Claude → PM |
| `telegram-bot/bot/messages.py` | Добавить юмор, stage info, extract_task_id |
| `telegram-bot/bot/handlers/pm.py` | Создать новый файл |
| `telegram-bot/services/youtrack.py` | Создать новый файл |
| `telegram-bot/app.py` | Добавить PM handlers, закомментить Claude |
| `telegram-bot/bot/handlers/claude.py` | Добавить deprecated комментарий |
| `telegram-bot/bot/handlers/gitlab_webhook.py` | Обновить для передачи commit message |

### 5.2 Новые переменные окружения

```bash
YOUTRACK_URL=http://192.168.1.74:8088
YOUTRACK_TOKEN=perm:xxx  # Нужно создать в YouTrack
YOUTRACK_PROJECT=WH
```

### 5.3 Тестирование

1. **PM меню:** Нажать "📋 PM" → проверить меню
2. **Статус агента:** PM → Статус → должен показать состояние
3. **Аудит:** PM → Аудит → должен загрузить стори из YouTrack
4. **Отчёт:** PM → Отчёт → День/Неделя → должен сгенерировать
5. **GitLab:** Запустить pipeline → проверить что парсится WH-xxx
6. **Юмор:** Проверить что шутки разнообразнее

---

## Оценка задач

| Задача | Сложность | Приоритет |
|--------|-----------|-----------|
| PM меню и клавиатуры | Низкая | Высокий |
| PM handler (статус) | Средняя | Высокий |
| YouTrack сервис | Средняя | Высокий |
| Аудит сторей | Средняя | Высокий |
| Отчёты день/неделя | Средняя | Высокий |
| GitLab улучшения | Низкая | Средний |
| Юмор | Низкая | Низкий |
| Claude Proxy /status | Низкая | Высокий |

---

## Зависимости

```
YouTrack Token → PM функции работают
Claude Proxy /status → Статус агента работает
GitLab webhook с commit data → Парсинг задач работает
```

---

*План готов! Жду утверждения для создания стори в YouTrack.*
