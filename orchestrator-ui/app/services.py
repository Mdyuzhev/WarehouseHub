"""
🔧 Сервисы для выполнения операций
Здесь вся магия деплоя и прочего
"""

import asyncio
import subprocess
import httpx
from datetime import datetime
from typing import Optional, AsyncGenerator
import random

from .config import SCRIPTS_DIR, SERVICES, MESSAGES
from .database import log_operation, update_operation


def get_random_message(category: str) -> str:
    """Получить случайное сообщение из категории"""
    messages = MESSAGES.get(category, ["Что-то происходит..."])
    return random.choice(messages)


async def run_script(script_name: str, *args) -> tuple[int, str, str]:
    """
    Запустить скрипт из папки scripts/
    Возвращает (return_code, stdout, stderr)
    """
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        return (1, "", f"Скрипт {script_name} не найден! 👻")

    cmd = ["bash", str(script_path)] + list(args)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    return (
        process.returncode,
        stdout.decode('utf-8'),
        stderr.decode('utf-8')
    )


async def stream_script(script_name: str, *args) -> AsyncGenerator[str, None]:
    """
    Запустить скрипт и стримить вывод построчно
    Для WebSocket вывода в реальном времени
    """
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        yield f"❌ Скрипт {script_name} не найден!"
        return

    cmd = ["bash", str(script_path)] + list(args)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    async for line in process.stdout:
        yield line.decode('utf-8').rstrip()

    await process.wait()

    if process.returncode == 0:
        yield f"\n✅ Готово! Exit code: 0"
    else:
        yield f"\n❌ Ошибка! Exit code: {process.returncode}"


async def check_service_health(service_key: str) -> dict:
    """Проверить здоровье сервиса"""
    service = SERVICES.get(service_key)
    if not service:
        return {"status": "unknown", "message": "Сервис не найден"}

    # Для сервисов без HTTP endpoint проверяем через kubectl
    if not service.get("url"):
        return await check_pod_status(service["name"], service["namespace"])

    url = service["url"] + service.get("health_endpoint", "/")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                return {
                    "status": "live",
                    "message": "Работает как часы! ⏰",
                    "response_time": response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    "status": "degraded",
                    "message": f"Отвечает, но странно... HTTP {response.status_code}",
                    "response_time": response.elapsed.total_seconds() * 1000
                }

    except httpx.TimeoutException:
        return {"status": "down", "message": "Таймаут! Сервис думает слишком долго 🐌"}
    except httpx.ConnectError:
        return {"status": "down", "message": "Не могу подключиться 💀"}
    except Exception as e:
        return {"status": "error", "message": f"Что-то пошло не так: {str(e)}"}


async def check_pod_status(name: str, namespace: str) -> dict:
    """Проверить статус пода через kubectl"""
    try:
        process = await asyncio.create_subprocess_exec(
            "kubectl", "get", "pods", "-n", namespace,
            "-l", f"app={name}",
            "-o", "jsonpath={.items[0].status.phase}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        phase = stdout.decode().strip()

        if phase == "Running":
            return {"status": "live", "message": "Под работает! 🏃"}
        elif phase == "Pending":
            return {"status": "loading", "message": "Запускается... 🔄"}
        elif phase:
            return {"status": "degraded", "message": f"Статус: {phase}"}
        else:
            return {"status": "down", "message": "Под не найден 👻"}

    except Exception as e:
        return {"status": "error", "message": f"kubectl сломался: {str(e)}"}


async def get_all_services_status() -> dict:
    """Получить статус всех сервисов"""
    results = {}

    tasks = [check_service_health(key) for key in SERVICES.keys()]
    statuses = await asyncio.gather(*tasks)

    for key, status in zip(SERVICES.keys(), statuses):
        results[key] = {
            **SERVICES[key],
            **status
        }

    return results


async def deploy_service(service: str, environment: str = "staging") -> dict:
    """
    Деплой сервиса
    service: api, frontend, all
    environment: staging, production
    """
    operation_id = await log_operation(f"deploy_{service}_{environment}", "running")

    script_map = {
        "api": "deploy-api.sh",
        "frontend": "deploy-frontend.sh",
        "all": "deploy-all.sh"
    }

    script = script_map.get(service)
    if not script:
        await update_operation(operation_id, "error", f"Неизвестный сервис: {service}")
        return {"success": False, "message": f"Сервис {service} не существует! 🤔"}

    code, stdout, stderr = await run_script(script, environment)

    if code == 0:
        await update_operation(operation_id, "success", stdout)
        return {
            "success": True,
            "message": get_random_message("deploy_success"),
            "output": stdout
        }
    else:
        await update_operation(operation_id, "error", stderr or stdout)
        return {
            "success": False,
            "message": get_random_message("deploy_fail"),
            "output": stderr or stdout
        }


async def run_tests(test_type: str = "e2e") -> dict:
    """Запуск тестов"""
    operation_id = await log_operation(f"tests_{test_type}", "running")

    script_map = {
        "e2e": "run-e2e-tests.sh",
        "load": "run-load-tests.sh",
        "unit": "run-unit-tests.sh"
    }

    script = script_map.get(test_type)
    if not script:
        await update_operation(operation_id, "error", f"Неизвестный тип тестов: {test_type}")
        return {"success": False, "message": f"Тип тестов {test_type} не поддерживается"}

    code, stdout, stderr = await run_script(script)

    if code == 0:
        await update_operation(operation_id, "success", stdout)
        return {
            "success": True,
            "message": get_random_message("tests_success"),
            "output": stdout
        }
    else:
        await update_operation(operation_id, "error", stderr or stdout)
        return {
            "success": False,
            "message": get_random_message("tests_fail"),
            "output": stderr or stdout
        }


async def get_logs(service: str, lines: int = 100) -> str:
    """Получить логи сервиса"""
    service_info = SERVICES.get(service)
    if not service_info:
        return f"❌ Сервис {service} не найден!"

    try:
        process = await asyncio.create_subprocess_exec(
            "kubectl", "logs",
            "-n", service_info["namespace"],
            "-l", f"app={service_info['name']}",
            "--tail", str(lines),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout.decode('utf-8')
        else:
            return f"❌ Ошибка: {stderr.decode('utf-8')}"

    except Exception as e:
        return f"❌ Не удалось получить логи: {str(e)}"


async def restart_service(service: str) -> dict:
    """Рестарт сервиса"""
    service_info = SERVICES.get(service)
    if not service_info:
        return {"success": False, "message": f"Сервис {service} не найден!"}

    operation_id = await log_operation(f"restart_{service}", "running")

    try:
        process = await asyncio.create_subprocess_exec(
            "kubectl", "rollout", "restart",
            "deployment", service_info["name"],
            "-n", service_info["namespace"],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            await update_operation(operation_id, "success", stdout.decode())
            return {
                "success": True,
                "message": f"🔄 {service_info['name']} перезапускается!",
                "output": stdout.decode()
            }
        else:
            await update_operation(operation_id, "error", stderr.decode())
            return {
                "success": False,
                "message": "Не удалось перезапустить 😢",
                "output": stderr.decode()
            }

    except Exception as e:
        await update_operation(operation_id, "error", str(e))
        return {"success": False, "message": f"Ошибка: {str(e)}"}
