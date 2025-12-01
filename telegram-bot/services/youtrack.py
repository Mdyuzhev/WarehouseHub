"""
YouTrack API интеграция.
Аудит стори, отчёты и прочая PM магия! 📊

API: Basic Auth (не OAuth/Token - они не работают в этой версии YouTrack)
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional
from config import YOUTRACK_URL, YOUTRACK_USER, YOUTRACK_PASSWORD, YOUTRACK_PROJECT

logger = logging.getLogger(__name__)

# HTTP client с Basic Auth
def get_auth():
    """Возвращает Basic Auth tuple."""
    return (YOUTRACK_USER, YOUTRACK_PASSWORD)


async def get_open_stories() -> dict:
    """
    Получает все открытые User Stories из YouTrack.

    Returns:
        {
            "success": bool,
            "stories": [
                {"id": "WH-88", "summary": "...", "state": "Open", "priority": "Major", ...}
            ],
            "count": int,
            "error": str (if failed)
        }
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Запрос открытых сторей
            response = await client.get(
                f"{YOUTRACK_URL}/api/issues",
                params={
                    "query": f"project:{YOUTRACK_PROJECT} State:Open Type:{{User Story}}",
                    "fields": "id,idReadable,summary,created,updated,customFields(name,value(name))"
                },
                auth=get_auth()
            )

            if response.status_code != 200:
                logger.error(f"YouTrack API error: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "stories": [], "count": 0}

            issues = response.json()
            stories = []

            for issue in issues:
                story = {
                    "id": issue.get("idReadable", "?"),
                    "summary": issue.get("summary", "No summary"),
                    "created": issue.get("created"),
                    "updated": issue.get("updated"),
                    "state": "Open",
                    "priority": "Normal",
                    "type": "User Story",
                }

                # Парсим custom fields
                for field in issue.get("customFields", []):
                    name = field.get("name")
                    value = field.get("value")

                    if value and isinstance(value, dict):
                        value = value.get("name", "")
                    elif value is None:
                        value = ""

                    if name == "Priority":
                        story["priority"] = value
                    elif name == "State":
                        story["state"] = value
                    elif name == "Type":
                        story["type"] = value
                    elif name == "Assignee":
                        story["assignee"] = value

                stories.append(story)

            logger.info(f"Got {len(stories)} open stories from YouTrack")
            return {"success": True, "stories": stories, "count": len(stories)}

    except Exception as e:
        logger.error(f"YouTrack API error: {e}")
        return {"success": False, "error": str(e), "stories": [], "count": 0}


async def get_issue_by_id(issue_id: str) -> dict:
    """
    Получает информацию о задаче по ID.

    Args:
        issue_id: ID задачи (например, "WH-88")

    Returns:
        {"success": bool, "issue": {...}, "error": str}
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{YOUTRACK_URL}/api/issues/{issue_id}",
                params={
                    "fields": "id,idReadable,summary,description,created,updated,customFields(name,value(name))"
                },
                auth=get_auth()
            )

            if response.status_code == 404:
                return {"success": False, "error": "Issue not found", "issue": None}

            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}", "issue": None}

            data = response.json()

            issue = {
                "id": data.get("idReadable", issue_id),
                "summary": data.get("summary", ""),
                "description": data.get("description", ""),
                "created": data.get("created"),
                "updated": data.get("updated"),
                "state": "Unknown",
                "priority": "Normal",
                "type": "Task",
            }

            # Парсим custom fields
            for field in data.get("customFields", []):
                name = field.get("name")
                value = field.get("value")

                if value and isinstance(value, dict):
                    value = value.get("name", "")
                elif value is None:
                    value = ""

                if name == "Priority":
                    issue["priority"] = value
                elif name == "State":
                    issue["state"] = value
                elif name == "Type":
                    issue["type"] = value
                elif name == "Assignee":
                    issue["assignee"] = value

            return {"success": True, "issue": issue}

    except Exception as e:
        logger.error(f"YouTrack get issue error: {e}")
        return {"success": False, "error": str(e), "issue": None}


async def get_activity_report(days: int = 1) -> dict:
    """
    Получает отчёт по активности за указанный период.

    Args:
        days: Количество дней (1 = сегодня, 7 = неделя)

    Returns:
        {
            "success": bool,
            "completed": [...],  # Завершённые задачи
            "in_progress": [...],  # В работе
            "started": [...],  # Начатые (Open -> In Progress)
            "silent": [...],  # Без активности (updated давно)
            "error": str
        }
    """
    try:
        # Вычисляем дату начала периода
        since = datetime.now() - timedelta(days=days)
        since_ts = int(since.timestamp() * 1000)  # YouTrack использует миллисекунды

        async with httpx.AsyncClient(timeout=20.0) as client:
            # Получаем все задачи проекта
            response = await client.get(
                f"{YOUTRACK_URL}/api/issues",
                params={
                    "query": f"project:{YOUTRACK_PROJECT}",
                    "fields": "id,idReadable,summary,created,updated,resolved,customFields(name,value(name))"
                },
                auth=get_auth()
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "completed": [], "in_progress": [], "started": [], "silent": []
                }

            issues = response.json()

            completed = []
            in_progress = []
            started = []
            silent = []

            for issue in issues:
                issue_data = {
                    "id": issue.get("idReadable", "?"),
                    "summary": issue.get("summary", ""),
                    "updated": issue.get("updated"),
                    "resolved": issue.get("resolved"),
                }

                state = "Unknown"
                for field in issue.get("customFields", []):
                    if field.get("name") == "State":
                        value = field.get("value")
                        if value and isinstance(value, dict):
                            state = value.get("name", "")
                        break

                issue_data["state"] = state
                updated_ts = issue.get("updated", 0)
                resolved_ts = issue.get("resolved")

                # Категоризация
                if state in ["Done", "Verified", "Closed"]:
                    # Завершённые в период
                    if resolved_ts and resolved_ts >= since_ts:
                        completed.append(issue_data)
                elif state in ["In Progress", "In Review"]:
                    in_progress.append(issue_data)
                    # Проверяем тишину (не обновлялось 3+ дней)
                    if updated_ts < (datetime.now() - timedelta(days=3)).timestamp() * 1000:
                        silent.append(issue_data)
                elif state == "Open":
                    # Проверяем, было ли начато в период (created в период)
                    created_ts = issue.get("created", 0)
                    if created_ts >= since_ts:
                        started.append(issue_data)

            return {
                "success": True,
                "completed": completed,
                "in_progress": in_progress,
                "started": started,
                "silent": silent,
                "period_days": days,
            }

    except Exception as e:
        logger.error(f"YouTrack activity report error: {e}")
        return {
            "success": False,
            "error": str(e),
            "completed": [], "in_progress": [], "started": [], "silent": []
        }


def parse_issue_id(text: str) -> Optional[str]:
    """
    Извлекает ID задачи (WH-xxx) из текста.

    Ищет в ветках, коммитах и т.д.
    Примеры:
        "feature/WH-88-pm-functions" -> "WH-88"
        "WH-88: Fix bug" -> "WH-88"
        "Fix WH-88 issue" -> "WH-88"
    """
    import re

    # Паттерн для поиска WH-XXX
    pattern = r'\b(WH-\d+)\b'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return match.group(1).upper()

    return None
