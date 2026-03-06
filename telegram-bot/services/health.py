"""
Health check сервисы.
Проверяем docker-compose сервисы и production.
"""

import httpx
from datetime import datetime
from config import (
    STAGING_API_URL, STAGING_FRONTEND_URL,
    PROD_API_URL, PROD_FRONTEND_URL,
    PROMETHEUS_URL,
    # WH-180: таймауты из конфига
    HEALTH_CHECK_TIMEOUT, PROMETHEUS_TIMEOUT,
    # WH-181: константы
    PROMETHEUS_QUERY_WINDOW
)


async def check_service_health(url: str, name: str) -> dict:
    """Проверяет здоровье сервиса по URL."""
    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT, verify=False) as client:
            start = datetime.now()
            # Для API проверяем /actuator/health, для frontend - просто корень
            if "api" in url.lower():
                check_url = f"{url}/actuator/health"
            else:
                check_url = url
            response = await client.get(check_url)
            latency = (datetime.now() - start).total_seconds() * 1000

            if response.status_code == 200:
                if "api" in url.lower():
                    data = response.json()
                    return {
                        "name": name,
                        "status": "UP",
                        "latency_ms": round(latency),
                        "details": data.get("components", {})
                    }
                else:
                    return {
                        "name": name,
                        "status": "UP",
                        "latency_ms": round(latency),
                        "details": {}
                    }
            else:
                return {"name": name, "status": "DOWN", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"name": name, "status": "DOWN", "error": str(e)[:50]}


async def get_k8s_resources() -> dict:
    """Получает информацию о docker-compose сервисах через HTTP проверки."""
    pods = []

    # Проверяем API и получаем статус БД
    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT) as client:
            response = await client.get(f"{STAGING_API_URL}/actuator/health")
            if response.status_code == 200:
                data = response.json()
                pods.append({"name": "warehouse-api", "status": "Running", "restarts": "0"})
                # Проверяем БД из ответа API
                db_status = data.get("components", {}).get("db", {}).get("status", "DOWN")
                pods.append({
                    "name": "postgresql",
                    "status": "Running" if db_status == "UP" else "Error",
                    "restarts": "0"
                })
            else:
                pods.append({"name": "warehouse-api", "status": "Error", "restarts": "?"})
                pods.append({"name": "postgresql", "status": "Unknown", "restarts": "?"})
    except:
        pods.append({"name": "warehouse-api", "status": "Unknown", "restarts": "?"})
        pods.append({"name": "postgresql", "status": "Unknown", "restarts": "?"})

    # Проверяем Frontend
    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT) as client:
            response = await client.get(f"{STAGING_FRONTEND_URL}")
            status = "Running" if response.status_code == 200 else "Error"
            pods.append({"name": "warehouse-frontend", "status": status, "restarts": "0"})
    except:
        pods.append({"name": "warehouse-frontend", "status": "Unknown", "restarts": "?"})

    # Prometheus метрики (skip if URL is empty)
    node_info = {}
    if PROMETHEUS_URL:
        try:
            async with httpx.AsyncClient(timeout=PROMETHEUS_TIMEOUT) as client:
                cpu_query = f'100 - (avg(rate(node_cpu_seconds_total{{mode="idle"}}[{PROMETHEUS_QUERY_WINDOW}])) * 100)'
                response = await client.get(
                    f"{PROMETHEUS_URL}/api/v1/query",
                    params={"query": cpu_query}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("result"):
                        cpu_value = float(data["data"]["result"][0]["value"][1])
                        node_info["cpu_percent"] = f"{cpu_value:.1f}%"

                mem_response = await client.get(
                    f"{PROMETHEUS_URL}/api/v1/query",
                    params={"query": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"}
                )
                if mem_response.status_code == 200:
                    mem_data = mem_response.json()
                    if mem_data.get("data", {}).get("result"):
                        mem_value = float(mem_data["data"]["result"][0]["value"][1])
                        node_info["memory_percent"] = f"{mem_value:.1f}%"
        except:
            pass

    return {"pods": pods, "node": node_info}


async def get_prod_resources() -> dict:
    """Получает информацию о production через HTTP проверки."""
    containers = []

    # Проверяем API
    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT, verify=False) as client:
            response = await client.get(f"{PROD_API_URL}/actuator/health")
            if response.status_code == 200:
                data = response.json()
                db_status = data.get("components", {}).get("db", {}).get("status", "?")
                containers.append({"name": "warehouse-api", "status": "UP"})
                containers.append({"name": "postgresql", "status": "UP" if db_status == "UP" else "DOWN"})
            else:
                containers.append({"name": "warehouse-api", "status": "DOWN"})
    except:
        containers.append({"name": "warehouse-api", "status": "DOWN"})

    # Проверяем Frontend
    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT, verify=False) as client:
            response = await client.get(f"{PROD_FRONTEND_URL}")
            containers.append({
                "name": "warehouse-frontend",
                "status": "UP" if response.status_code == 200 else "DOWN"
            })
    except:
        containers.append({"name": "warehouse-frontend", "status": "DOWN"})

    # nginx
    containers.append({"name": "nginx", "status": "UP" if containers else "DOWN"})

    return {"containers": containers, "memory": ""}


async def check_all_health() -> dict:
    """Проверяет здоровье всех сервисов."""
    import asyncio

    staging_api, staging_fe, prod_api, prod_fe, k8s, prod = await asyncio.gather(
        check_service_health(STAGING_API_URL, "Staging API"),
        check_service_health(STAGING_FRONTEND_URL, "Staging Frontend"),
        check_service_health(PROD_API_URL, "Production API"),
        check_service_health(PROD_FRONTEND_URL, "Production Frontend"),
        get_k8s_resources(),
        get_prod_resources()
    )

    return {
        "staging_api": staging_api,
        "staging_fe": staging_fe,
        "prod_api": prod_api,
        "prod_fe": prod_fe,
        "k8s": k8s,
        "prod": prod,
    }
