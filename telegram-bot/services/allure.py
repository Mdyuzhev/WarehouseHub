"""
Allure отчёты.
Показываем красивые картинки с тестами! 📊
"""

import logging
import httpx
from config import ALLURE_SERVER_URL, ALLURE_PUBLIC_URL

logger = logging.getLogger(__name__)


async def get_allure_report_stats() -> dict:
    """Получает краткую статистику последнего отчёта."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{ALLURE_SERVER_URL}/allure-docker-service/projects/warehouse-api/reports/latest/widgets/summary.json"
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "statistic": data.get("statistic", {}),
                    "time": data.get("time", {})
                }

            return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        logger.error(f"Allure stats error: {e}")
        return {"success": False, "error": str(e)[:100]}


async def get_allure_report_details(project_id: str = "warehouse-api") -> dict:
    """
    Получает детальную статистику последнего отчёта.

    Args:
        project_id: ID проекта в Allure (e2e-staging, e2e-prod, ui-staging, ui-prod)
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Получаем summary
            summary_resp = await client.get(
                f"{ALLURE_SERVER_URL}/allure-docker-service/projects/{project_id}/reports/latest/widgets/summary.json"
            )

            if summary_resp.status_code != 200:
                logger.warning(f"Allure summary for {project_id}: HTTP {summary_resp.status_code}")
                return None

            summary = summary_resp.json()

            # Пробуем получить duration
            try:
                duration_resp = await client.get(
                    f"{ALLURE_SERVER_URL}/allure-docker-service/projects/{project_id}/reports/latest/widgets/duration.json"
                )
                if duration_resp.status_code == 200:
                    duration_data = duration_resp.json()
                    summary["duration"] = duration_data.get("data", {}).get("duration", 0)
            except:
                pass

            return summary

    except Exception as e:
        logger.error(f"Allure details error for {project_id}: {e}")
        return None


def get_allure_report_url(project_id: str = "warehouse-api") -> str:
    """
    Возвращает публичный URL последнего отчёта (для ссылок в Telegram).

    Args:
        project_id: ID проекта в Allure (e2e-staging, e2e-prod, ui-staging, ui-prod)
    """
    return f"{ALLURE_PUBLIC_URL}/allure-docker-service/projects/{project_id}/reports/latest/index.html"
