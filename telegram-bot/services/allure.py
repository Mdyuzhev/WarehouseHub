"""
Allure отчёты.
Показываем красивые картинки с тестами! 📊
"""

import logging
import httpx
from config import ALLURE_SERVER_URL

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


async def get_allure_report_details() -> dict:
    """Получает детальную статистику последнего отчёта."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Получаем summary
            summary_resp = await client.get(
                f"{ALLURE_SERVER_URL}/allure-docker-service/projects/warehouse-api/reports/latest/widgets/summary.json"
            )

            if summary_resp.status_code != 200:
                return None

            summary = summary_resp.json()

            # Пробуем получить duration
            try:
                duration_resp = await client.get(
                    f"{ALLURE_SERVER_URL}/allure-docker-service/projects/warehouse-api/reports/latest/widgets/duration.json"
                )
                if duration_resp.status_code == 200:
                    duration_data = duration_resp.json()
                    summary["duration"] = duration_data.get("data", {}).get("duration", 0)
            except:
                pass

            return summary

    except Exception as e:
        logger.error(f"Allure details error: {e}")
        return None


def get_allure_report_url() -> str:
    """Возвращает URL последнего отчёта."""
    return f"{ALLURE_SERVER_URL}/allure-docker-service/projects/warehouse-api/reports/latest"
