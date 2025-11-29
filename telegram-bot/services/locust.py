"""
Locust нагрузочное тестирование.
Мучаем сервера по-взрослому! 🔥
"""

import logging
import httpx
from config import LOCUST_MASTER_URL

logger = logging.getLogger(__name__)


async def start_load_test(target_url: str, users: int, spawn_rate: int) -> dict:
    """
    Запускает нагрузочный тест через Locust API.

    Returns:
        dict с полями: success, error
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{LOCUST_MASTER_URL}/swarm",
                data={
                    "user_count": users,
                    "spawn_rate": spawn_rate,
                    "host": target_url,
                }
            )

            if response.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        logger.error(f"Locust start error: {e}")
        return {"success": False, "error": str(e)[:100]}


async def stop_load_test() -> dict:
    """Останавливает нагрузочный тест."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LOCUST_MASTER_URL}/stop")

            if response.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        logger.error(f"Locust stop error: {e}")
        return {"success": False, "error": str(e)[:100]}


async def get_load_test_stats() -> dict:
    """Получает текущую статистику нагрузочного теста."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LOCUST_MASTER_URL}/stats/requests")

            if response.status_code == 200:
                data = response.json()
                stats = data.get("stats", [])

                # Ищем агрегированную статистику
                aggregated = None
                for stat in stats:
                    if stat.get("name") == "Aggregated":
                        aggregated = stat
                        break

                if aggregated:
                    return {
                        "success": True,
                        "total_requests": aggregated.get("num_requests", 0),
                        "total_failures": aggregated.get("num_failures", 0),
                        "avg_response_time": round(aggregated.get("avg_response_time", 0)),
                        "min_response_time": round(aggregated.get("min_response_time", 0)),
                        "max_response_time": round(aggregated.get("max_response_time", 0)),
                        "current_rps": round(aggregated.get("current_rps", 0), 1),
                        "current_fail_per_sec": round(aggregated.get("current_fail_per_sec", 0), 2),
                    }
                else:
                    return {"success": True, "message": "No stats yet"}

            return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        logger.error(f"Locust stats error: {e}")
        return {"success": False, "error": str(e)[:100]}


async def reset_load_test_stats() -> dict:
    """Сбрасывает статистику нагрузочного теста."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LOCUST_MASTER_URL}/stats/reset")

            if response.status_code == 200:
                return {"success": True}
            return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        return {"success": False, "error": str(e)[:100]}


def calculate_spawn_rate(users: int, ramp_up: str) -> int:
    """Рассчитывает spawn_rate в зависимости от паттерна."""
    if ramp_up == "instant":
        return users  # Все сразу
    elif ramp_up == "fast":
        return max(users // 5, 1)  # 20% в секунду
    elif ramp_up == "step":
        return max(users // 10, 1)  # Для ступенчатого - медленнее
    else:  # smooth
        return max(users // 10, 1)  # 10% в секунду
