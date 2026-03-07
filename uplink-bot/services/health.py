"""
Health check services.
Docker-compose services and Prometheus metrics.
"""

import httpx
from datetime import datetime
from config import (
    STAGING_API_URL, STAGING_FRONTEND_URL,
    PROMETHEUS_URL,
    HEALTH_CHECK_TIMEOUT, PROMETHEUS_TIMEOUT,
)


async def check_service_health(url: str, name: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT, verify=False) as client:
            start = datetime.now()
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
                    return {"name": name, "status": "UP", "latency_ms": round(latency), "details": {}}
            else:
                return {"name": name, "status": "DOWN", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"name": name, "status": "DOWN", "error": str(e)[:50]}


async def get_k8s_resources() -> dict:
    """Gets docker-compose service info and Prometheus metrics."""
    pods = []

    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT) as client:
            response = await client.get(f"{STAGING_API_URL}/actuator/health")
            if response.status_code == 200:
                data = response.json()
                pods.append({"name": "warehouse-api", "status": "Running", "restarts": "0"})
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

    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT) as client:
            response = await client.get(f"{STAGING_FRONTEND_URL}")
            status = "Running" if response.status_code == 200 else "Error"
            pods.append({"name": "warehouse-frontend", "status": status, "restarts": "0"})
    except:
        pods.append({"name": "warehouse-frontend", "status": "Unknown", "restarts": "?"})

    node_info = {}
    if PROMETHEUS_URL:
        try:
            async with httpx.AsyncClient(timeout=PROMETHEUS_TIMEOUT) as client:
                response = await client.get(
                    f"{PROMETHEUS_URL}/api/v1/query",
                    params={"query": "system_cpu_usage * 100"}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data", {}).get("result"):
                        cpu_value = float(data["data"]["result"][0]["value"][1])
                        node_info["cpu_percent"] = f"{cpu_value:.1f}%"

                mem_response = await client.get(
                    f"{PROMETHEUS_URL}/api/v1/query",
                    params={"query": "sum(jvm_memory_used_bytes) / sum(jvm_memory_max_bytes) * 100"}
                )
                if mem_response.status_code == 200:
                    mem_data = mem_response.json()
                    if mem_data.get("data", {}).get("result"):
                        mem_value = float(mem_data["data"]["result"][0]["value"][1])
                        node_info["memory_percent"] = f"{mem_value:.1f}%"
        except:
            pass

    return {"pods": pods, "node": node_info}


async def check_all_health() -> dict:
    import asyncio

    staging_api, staging_fe, k8s = await asyncio.gather(
        check_service_health(STAGING_API_URL, "Staging API"),
        check_service_health(STAGING_FRONTEND_URL, "Staging Frontend"),
        get_k8s_resources(),
    )

    return {
        "staging_api": staging_api,
        "staging_fe": staging_fe,
        "k8s": k8s,
    }
