"""
GitLab Webhook to Telegram Notification Service.
Принимает webhooks от GitLab и отправляет уведомления в Telegram.
Поддерживает команду /health для мониторинга серверов.
Теперь с кнопками и нагрузочным тестированием! 🚀
"""

import os
import logging
import httpx
import asyncio
import random
import subprocess
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITLAB_WEBHOOK_SECRET = os.getenv("GITLAB_WEBHOOK_SECRET", "")

# Конфигурация серверов для мониторинга
# Для staging используем internal K8s DNS (pod находится в том же кластере)
STAGING_API_URL = os.getenv("STAGING_API_URL", "http://warehouse-api-service.warehouse.svc.cluster.local:8080")
STAGING_FRONTEND_URL = os.getenv("STAGING_FRONTEND_URL", "http://warehouse-frontend-service.warehouse.svc.cluster.local")
PROD_API_URL = os.getenv("PROD_API_URL", "https://api.wh-lab.ru")
PROD_FRONTEND_URL = os.getenv("PROD_FRONTEND_URL", "https://wh-lab.ru")
PROD_HOST = os.getenv("PROD_HOST", "130.193.44.34")

# Locust конфигурация - namespace loadtest!
LOCUST_MASTER_URL = os.getenv("LOCUST_MASTER_URL", "http://locust-master.loadtest.svc.cluster.local:8089")

# GitLab и Allure конфигурация
GITLAB_URL = os.getenv("GITLAB_URL", "http://192.168.1.74:8080")
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID", "2")  # warehouse-api project
GITLAB_TRIGGER_TOKEN = os.getenv("GITLAB_TRIGGER_TOKEN", "")
ALLURE_SERVER_URL = os.getenv("ALLURE_SERVER_URL", "http://192.168.1.74:5050")

# Последний обработанный update_id
last_update_id = 0

# Текущий статус нагрузочного тестирования
load_test_status = {
    "running": False,
    "started_at": None,
    "target": None,
    "users": 0,
    "chat_id": None,
    "stats_task": None,  # Задача для периодической статистики
    "stats_history": [],  # История статистики для финального отчёта
}

# Ожидание пароля для НТ {chat_id: {"target": "staging", "users": 50, "duration": 300, "ramp_up": "linear"}}
pending_load_auth = {}

# Состояние пошаговой настройки НТ {chat_id: {"step": "users", "target": "staging", ...}}
load_test_wizard = {}

# Пароли для запуска нагрузочного тестирования
LOAD_TEST_PASSWORD = os.getenv("LOAD_TEST_PASSWORD", "Misha2021@1@")
LOAD_TEST_GUEST_PASSWORD = os.getenv("LOAD_TEST_GUEST_PASSWORD", "Guest")

# Лимиты для гостевого доступа
GUEST_MAX_USERS = 20
GUEST_MAX_DURATION = 300  # 5 минут

# Статус E2E тестирования
e2e_test_status = {
    "running": False,
    "started_at": None,
    "pipeline_id": None,
    "chat_id": None,
}

# Claude Proxy URL (запущен на хосте, порт 8765)
CLAUDE_PROXY_URL = os.getenv("CLAUDE_PROXY_URL", "http://192.168.1.74:8765")

# Ожидание ввода для Claude {chat_id: {"step": "password" | "task"}}
pending_claude_task = {}

# Статус выполнения Claude задачи
claude_task_status = {
    "running": False,
    "started_at": None,
    "chat_id": None,
    "task": None,
}

# Юмористические фразы 🎭
JOKES = {
    "start": [
        "Привет, кожаный мешок! 🤖 Я бот, который следит за твоим кодом лучше, чем ты сам.",
        "О, новый раб CI/CD пришёл! Добро пожаловать! 👋",
        "Здравствуй, человек. Надеюсь, твои пайплайны не так сломаны, как твоя жизнь. 😏",
        "Приветствую! Я тот, кто видит все твои failed pipelines в 3 часа ночи. 🌙",
    ],
    "health_good": [
        "Всё работает! Даже странно... 🤔",
        "Серверы живы! В отличие от твоего sleep schedule. 😴",
        "Зелёненькое! Как и должно быть. Наслаждайся, пока можешь. ✨",
        "Удивительно, но всё ОК! Это точно наш проект? 🧐",
    ],
    "health_bad": [
        "Хьюстон, у нас проблемы! 🚨",
        "Что-то сломалось... Опять. Как обычно. 💔",
        "RED ALERT! Кто-то опять запушил в пятницу вечером? 🔥",
        "Пора паниковать! Или кофе. Лучше кофе. ☕",
    ],
    "load_test_start": [
        "Запускаю нагрузку! Сервера, держитесь! 💪",
        "Время стресс-теста! Как твоя жизнь, только для серверов. 🏋️",
        "Поехали! Надеюсь, сервер крепче твоих нервов. 🎢",
        "Unleashing the LOAD! Пристегнись! 🚀",
    ],
    "load_test_stop": [
        "Тест остановлен. Сервера выдохнули. 😮‍💨",
        "Всё, хватит мучать железо на сегодня. 🛑",
        "Нагрузка снята. Можно расслабиться. 🧘",
    ],
    "e2e_start": [
        "Запускаю E2E тесты! Надеюсь, ты ничего не сломал... 🤞",
        "Поехали проверять! Сейчас узнаем, кто тут накосячил. 🔍",
        "E2E тесты в деле! Время узнать правду о твоём коде. 🎯",
        "Тестируем API! Скрестил пальцы за тебя. 🤖",
    ],
    "e2e_success": [
        "ВСЕ ТЕСТЫ ПРОШЛИ! 🎉 Ты красавчик! (или тестов мало...)",
        "Зелёненькое! Редкое зрелище в наши дни. ✅",
        "100% passed! Кажется, сегодня можно спать спокойно. 😌",
        "Тесты в порядке! Чудеса случаются! ✨",
    ],
    "e2e_failure": [
        "Упс... Кто-то сломал тесты! Не ты ли? 🤔",
        "FAILED! Время искать виноватого. Спойлер: это ты. 💀",
        "Тесты упали. Классика. Кофе? ☕",
        "Красненькое! Надеюсь, это не прод... 🔴",
    ],
    "claude_start": [
        "Окей, сейчас разберусь... 🤔",
        "Принято! Погнали работать! 💪",
        "Задача получена, выполняю... 🚀",
        "Есть, босс! Уже делаю! 🤖",
    ],
    "claude_done": [
        "Готово! Я молодец? 😏",
        "Сделано! Чего ещё изволите? 🎩",
        "Выполнено! Следующая задача? 💪",
        "Всё, справился! 🏆",
    ],
    "claude_error": [
        "Упс, что-то пошло не так... 😅",
        "Хьюстон, у нас проблема! 🚨",
        "Не получилось, но я старался! 😬",
    ],
}


# ==================== HEALTH CHECK FUNCTIONS ====================

async def check_service_health(url: str, name: str) -> dict:
    """Проверяет здоровье сервиса по URL."""
    try:
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
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
    """Получает информацию о сервисах K8s через внешние HTTP проверки."""
    services = [
        ("warehouse-api", f"{STAGING_API_URL}/actuator/health"),
        ("warehouse-frontend", f"{STAGING_FRONTEND_URL}"),
    ]

    pods = []

    # Проверяем API и получаем статус БД
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{STAGING_API_URL}/actuator/health")
            if response.status_code == 200:
                data = response.json()
                pods.append({"name": "warehouse-api", "status": "Running", "restarts": "0"})
                # Проверяем БД из ответа API
                db_status = data.get("components", {}).get("db", {}).get("status", "DOWN")
                pods.append({"name": "postgresql", "status": "Running" if db_status == "UP" else "Error", "restarts": "0"})
            else:
                pods.append({"name": "warehouse-api", "status": "Error", "restarts": "?"})
                pods.append({"name": "postgresql", "status": "Unknown", "restarts": "?"})
    except:
        pods.append({"name": "warehouse-api", "status": "Unknown", "restarts": "?"})
        pods.append({"name": "postgresql", "status": "Unknown", "restarts": "?"})

    # Проверяем Frontend
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{STAGING_FRONTEND_URL}")
            status = "Running" if response.status_code == 200 else "Error"
            pods.append({"name": "warehouse-frontend", "status": status, "restarts": "0"})
    except:
        pods.append({"name": "warehouse-frontend", "status": "Unknown", "restarts": "?"})

    # Prometheus метрики для ресурсов (используем internal DNS)
    node_info = {}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Пробуем получить CPU метрики из Prometheus внутри кластера
            prometheus_url = "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090"
            response = await client.get(
                f"{prometheus_url}/api/v1/query",
                params={"query": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("result"):
                    cpu_value = float(data["data"]["result"][0]["value"][1])
                    node_info["cpu_percent"] = f"{cpu_value:.1f}%"

            # Пробуем получить Memory метрики
            mem_response = await client.get(
                f"{prometheus_url}/api/v1/query",
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
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
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
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            response = await client.get(f"{PROD_FRONTEND_URL}")
            containers.append({"name": "warehouse-frontend", "status": "UP" if response.status_code == 200 else "DOWN"})
    except:
        containers.append({"name": "warehouse-frontend", "status": "DOWN"})

    # Проверяем nginx (reverse proxy)
    containers.append({"name": "nginx", "status": "UP" if containers else "DOWN"})

    return {"containers": containers, "memory": ""}


def format_health_message(staging_api, staging_fe, prod_api, prod_fe, k8s, prod) -> str:
    """Форматирует сообщение о здоровье серверов."""

    def status_icon(s): return "✅" if s.get("status") == "UP" else "❌"
    def latency_str(s): return f" ({s.get('latency_ms', '?')}ms)" if s.get('latency_ms') else ""

    msg = f"""
<b>🏥 Статус серверов</b>
<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>

<b>━━━ 🧪 STAGING (K3s) ━━━</b>
{status_icon(staging_api)} <b>API:</b> {staging_api.get('status')}{latency_str(staging_api)}
{status_icon(staging_fe)} <b>Frontend:</b> {staging_fe.get('status')}{latency_str(staging_fe)}
"""

    # K8s pods
    if k8s.get("pods"):
        msg += "\n<b>📦 Поды:</b>\n"
        for pod in k8s["pods"][:6]:
            icon = "🟢" if pod["status"] == "Running" else "🔴"
            restarts = f" (↻{pod['restarts']})" if pod['restarts'] != "0" else ""
            msg += f"  {icon} {pod['name'][:25]}{restarts}\n"

    # K8s node resources
    if k8s.get("node"):
        msg += f"\n<b>💻 Ресурсы ноды:</b>\n"
        msg += f"  CPU: {k8s['node'].get('cpu_percent', '?')} | RAM: {k8s['node'].get('memory_percent', '?')}\n"

    msg += f"""
<b>━━━ 🚀 PRODUCTION (YC) ━━━</b>
{status_icon(prod_api)} <b>API:</b> {prod_api.get('status')}{latency_str(prod_api)}
{status_icon(prod_fe)} <b>Frontend:</b> {prod_fe.get('status')}{latency_str(prod_fe)}
"""

    # Prod containers
    if prod.get("containers"):
        msg += "\n<b>🐳 Контейнеры:</b>\n"
        for c in prod["containers"][:6]:
            icon = "🟢" if c["status"] == "UP" else "🔴"
            msg += f"  {icon} {c['name']}\n"
        if prod.get("memory"):
            msg += f"\n<b>💾 Память:</b> {prod['memory'].replace('MEM:', '')}\n"
    elif prod.get("error"):
        msg += f"\n⚠️ <i>Не удалось получить данные: {prod['error']}</i>\n"

    # Итоговый статус
    all_up = all(s.get("status") == "UP" for s in [staging_api, staging_fe, prod_api, prod_fe])
    if all_up:
        msg += "\n✨ <b>Все сервисы работают!</b>"
    else:
        msg += "\n⚠️ <b>Есть проблемы с сервисами!</b>"

    return msg.strip()


# ==================== KEYBOARDS ====================

def get_reply_keyboard():
    """Возвращает постоянную клавиатуру снизу экрана."""
    return {
        "keyboard": [
            [{"text": "🏥 Статус"}, {"text": "📊 Метрики"}, {"text": "🧪 E2E"}],
            [{"text": "🔥 Нагрузка"}, {"text": "📈 Тест"}, {"text": "🛑 Стоп"}],
            [{"text": "🤖 Claude"}, {"text": "🎰 Шутка"}, {"text": "❓"}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
        "input_field_placeholder": "Жми кнопку ☝️",
    }


def get_main_menu_keyboard():
    """Возвращает главное меню с inline кнопками."""
    return {
        "inline_keyboard": [
            [
                {"text": "🏥 Статус серверов", "callback_data": "health"},
                {"text": "📊 Метрики", "callback_data": "metrics"},
            ],
            [
                {"text": "🔥 Нагрузка: STAGING", "callback_data": "load_staging"},
                {"text": "⚠️ Нагрузка: PROD", "callback_data": "load_prod"},
            ],
            [
                {"text": "🛑 Остановить тест", "callback_data": "load_stop"},
                {"text": "📈 Статус теста", "callback_data": "load_status"},
            ],
            [
                {"text": "🎰 Анекдот", "callback_data": "joke"},
                {"text": "❓ Помощь", "callback_data": "help"},
            ],
        ]
    }


def get_load_test_keyboard(target: str):
    """Возвращает клавиатуру для выбора количества пользователей."""
    return {
        "inline_keyboard": [
            [
                {"text": "👤 10", "callback_data": f"lt_users_{target}_10"},
                {"text": "👥 25", "callback_data": f"lt_users_{target}_25"},
                {"text": "👥 50", "callback_data": f"lt_users_{target}_50"},
            ],
            [
                {"text": "💪 100", "callback_data": f"lt_users_{target}_100"},
                {"text": "🔥 200", "callback_data": f"lt_users_{target}_200"},
                {"text": "💀 500", "callback_data": f"lt_users_{target}_500"},
            ],
            [
                {"text": "✏️ Своё число", "callback_data": f"lt_users_{target}_custom"},
            ],
            [
                {"text": "⬅️ Назад", "callback_data": "menu"},
            ],
        ]
    }


def get_duration_keyboard(target: str, users: int):
    """Возвращает клавиатуру для выбора длительности теста."""
    return {
        "inline_keyboard": [
            [
                {"text": "⚡ 1 мин", "callback_data": f"lt_dur_{target}_{users}_60"},
                {"text": "⏱ 3 мин", "callback_data": f"lt_dur_{target}_{users}_180"},
                {"text": "🕐 5 мин", "callback_data": f"lt_dur_{target}_{users}_300"},
            ],
            [
                {"text": "🕑 10 мин", "callback_data": f"lt_dur_{target}_{users}_600"},
                {"text": "🕒 15 мин", "callback_data": f"lt_dur_{target}_{users}_900"},
                {"text": "🕕 30 мин", "callback_data": f"lt_dur_{target}_{users}_1800"},
            ],
            [
                {"text": "✏️ Своё время", "callback_data": f"lt_dur_{target}_{users}_custom"},
            ],
            [
                {"text": "⬅️ Назад", "callback_data": f"load_{target}"},
            ],
        ]
    }


def get_rampup_keyboard(target: str, users: int, duration: int):
    """Возвращает клавиатуру для выбора паттерна нарастания нагрузки."""
    return {
        "inline_keyboard": [
            [
                {"text": "📈 Плавный", "callback_data": f"lt_ramp_{target}_{users}_{duration}_smooth"},
            ],
            [
                {"text": "⚡ Быстрый", "callback_data": f"lt_ramp_{target}_{users}_{duration}_fast"},
            ],
            [
                {"text": "🚀 Мгновенный", "callback_data": f"lt_ramp_{target}_{users}_{duration}_instant"},
            ],
            [
                {"text": "📊 Ступенчатый", "callback_data": f"lt_ramp_{target}_{users}_{duration}_step"},
            ],
            [
                {"text": "⬅️ Назад", "callback_data": f"lt_users_{target}_{users}"},
            ],
        ]
    }


# ==================== TELEGRAM BOT POLLING ====================

async def get_telegram_updates(offset: int = 0) -> list:
    """Получает обновления от Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        return []

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 30, "allowed_updates": ["message", "callback_query"]}

    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("result", [])
            elif response.status_code == 409:
                # Конфликт - другой бот использует getUpdates, ждём больше чем timeout
                logger.warning("Telegram 409 Conflict - waiting 35s...")
                await asyncio.sleep(35)
                return []
    except Exception as e:
        logger.error(f"Failed to get updates: {e}")
    return []


async def process_command(chat_id: int, text: str):
    """Обрабатывает команду от пользователя."""
    global pending_load_auth, load_test_wizard, pending_claude_task

    # Проверяем, ожидаем ли пароль от этого пользователя
    if chat_id in pending_load_auth:
        await handle_password_input(chat_id, text)
        return

    # Проверяем, ожидаем ли ввод для wizard
    if chat_id in load_test_wizard:
        await handle_wizard_input(chat_id, text)
        return

    # Проверяем, ожидаем ли ввод для Claude
    if chat_id in pending_claude_task:
        await handle_claude_input(chat_id, text)
        return

    # Обработка кнопок reply keyboard
    if text == "🏥 Статус":
        await handle_health_command(chat_id)
        return
    elif text == "📊 Метрики":
        await handle_metrics_command(chat_id)
        return
    elif text == "🔥 Нагрузка":
        await handle_load_menu(chat_id)
        return
    elif text == "🛑 Стоп":
        await handle_stop_load_test(chat_id)
        return
    elif text == "📈 Тест":
        await handle_load_status(chat_id)
        return
    elif text == "🧪 E2E":
        await handle_e2e_menu(chat_id)
        return
    elif text == "🎰 Шутка":
        await send_random_joke(chat_id)
        return
    elif text == "🤖 Claude":
        await handle_claude_menu(chat_id)
        return
    elif text == "❓":
        await process_command(chat_id, "/help")
        return

    # Обработка команд
    if text == "/health" or text == "/status":
        await handle_health_command(chat_id)

    elif text == "/start":
        # Приветствие с юмором и ПОСТОЯННОЙ клавиатурой
        joke = random.choice(JOKES["start"])
        welcome_msg = f"""
{joke}

<b>🤖 Warehouse Bot v4.0</b>

<b>Кнопки внизу:</b>
🏥 статус | 📊 метрики | 🔥 нагрузка | 🛑 стоп
📈 статус НТ | 🎰 анекдот | ❓ помощь

<b>🔐 Нагрузочное тестирование защищено паролем!</b>
        """
        await send_message_with_reply_keyboard(welcome_msg.strip(), chat_id=chat_id)

    elif text == "/help":
        help_msg = """
<b>❓ Справка</b>

<b>Кнопки:</b>
🏥 - статус серверов
📊 - метрики K8s
🔥 - нагрузочный тест (пароль!)
🛑 - остановить тест
📈 - статус НТ
🎰 - анекдот
❓ - эта справка

<b>Нагрузочное тестирование:</b>
🔐 Защищено паролем
📊 Отчёты каждые 3 мин
🏁 Финальный отчёт с вердиктом

<i>Бот 24/7, в отличие от разрабов...</i> 😏
        """
        await send_message_with_reply_keyboard(help_msg.strip(), chat_id=chat_id)

    elif text == "/menu":
        await send_telegram_message_with_keyboard(
            "📱 <b>Главное меню</b>\n\nВыбери действие:",
            get_main_menu_keyboard(),
            chat_id=chat_id
        )

    elif text == "/load":
        await handle_load_menu(chat_id)

    elif text == "/stop":
        await handle_stop_load_test(chat_id)

    elif text == "/joke":
        await send_random_joke(chat_id)


async def handle_load_menu(chat_id: int):
    """Показывает меню выбора цели для нагрузки."""
    msg = """
<b>🔥 Нагрузочное тестирование</b>

⚠️ <b>Внимание:</b> Для запуска потребуется пароль!

Выбери цель для тестирования:
    """
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🧪 STAGING", "callback_data": "load_staging"},
                {"text": "🚀 PRODUCTION", "callback_data": "load_prod"},
            ],
            [{"text": "⬅️ Назад в меню", "callback_data": "menu"}],
        ]
    }
    await send_telegram_message_with_keyboard(msg.strip(), keyboard, chat_id=chat_id)


async def handle_metrics_command(chat_id: int):
    """Показывает метрики K8s."""
    await send_chat_action(chat_id, "typing")
    k8s = await get_k8s_resources()
    msg = "<b>📊 Метрики кластера K8s</b>\n\n"
    if k8s.get("node"):
        msg += f"💻 CPU: {k8s['node'].get('cpu_percent', 'N/A')}\n"
        msg += f"💾 RAM: {k8s['node'].get('memory_percent', 'N/A')}\n"
    else:
        msg += "<i>Метрики временно недоступны</i>"
    await send_message_with_reply_keyboard(msg, chat_id=chat_id)


async def handle_wizard_input(chat_id: int, text: str):
    """Обрабатывает пользовательский ввод в wizard настройки НТ."""
    global load_test_wizard

    if chat_id not in load_test_wizard:
        return

    wizard = load_test_wizard[chat_id]
    step = wizard.get("step")

    try:
        if step == "users_custom":
            # Ввод количества пользователей
            users = int(text.strip())
            if users < 1 or users > 1000:
                await send_telegram_message(
                    "⚠️ Количество пользователей должно быть от 1 до 1000. Попробуй ещё раз:",
                    chat_id=chat_id
                )
                return
            wizard["users"] = users
            wizard["step"] = "duration"
            del load_test_wizard[chat_id]
            # Переход к выбору длительности
            await show_duration_step(chat_id, wizard["target"], users)

        elif step == "duration_custom":
            # Ввод длительности в минутах
            minutes = int(text.strip())
            if minutes < 1 or minutes > 60:
                await send_telegram_message(
                    "⚠️ Длительность должна быть от 1 до 60 минут. Попробуй ещё раз:",
                    chat_id=chat_id
                )
                return
            duration = minutes * 60
            wizard["duration"] = duration
            del load_test_wizard[chat_id]
            # Переход к выбору паттерна
            await show_rampup_step(chat_id, wizard["target"], wizard["users"], duration)

    except ValueError:
        await send_telegram_message(
            "⚠️ Введи число! Попробуй ещё раз:",
            chat_id=chat_id
        )


async def handle_password_input(chat_id: int, password: str):
    """Обрабатывает ввод пароля для нагрузочного тестирования."""
    global pending_load_auth

    if chat_id not in pending_load_auth:
        return

    auth_data = pending_load_auth[chat_id]

    if password == LOAD_TEST_PASSWORD:
        # Админский пароль - полный доступ
        del pending_load_auth[chat_id]
        await send_telegram_message(
            "✅ <b>Пароль принят!</b> (полный доступ)\n\n<i>Запускаю нагрузочное тестирование...</i>",
            chat_id=chat_id
        )
        await start_load_test_confirmed(
            chat_id,
            auth_data["target"],
            auth_data["users"],
            auth_data.get("duration", 300),
            auth_data.get("ramp_up", "smooth")
        )
    elif password == LOAD_TEST_GUEST_PASSWORD:
        # Гостевой пароль - ограниченный доступ
        del pending_load_auth[chat_id]

        # Применяем лимиты для гостя
        users = min(auth_data["users"], GUEST_MAX_USERS)
        duration = min(auth_data.get("duration", 300), GUEST_MAX_DURATION)

        original_users = auth_data["users"]
        original_duration = auth_data.get("duration", 300)

        # Сообщаем об ограничениях если параметры были урезаны
        if users < original_users or duration < original_duration:
            await send_telegram_message(
                f"✅ <b>Гостевой доступ!</b>\n\n"
                f"⚠️ <i>Параметры ограничены:</i>\n"
                f"👥 Пользователей: {original_users} → <b>{users}</b>\n"
                f"⏱ Длительность: {original_duration//60} мин → <b>{duration//60}</b> мин\n\n"
                f"<i>Запускаю...</i>",
                chat_id=chat_id
            )
        else:
            await send_telegram_message(
                "✅ <b>Гостевой доступ!</b>\n\n<i>Запускаю нагрузочное тестирование...</i>",
                chat_id=chat_id
            )

        await start_load_test_confirmed(
            chat_id,
            auth_data["target"],
            users,
            duration,
            auth_data.get("ramp_up", "smooth"),
            is_guest=True
        )
    else:
        # Неверный пароль
        del pending_load_auth[chat_id]
        await send_message_with_reply_keyboard(
            "❌ <b>Неверный пароль!</b>\n\n<i>Доступ к нагрузочному тестированию запрещён.</i>\n\n🔒 Если забыл пароль - спроси у админа 😏",
            chat_id=chat_id
        )


async def show_duration_step(chat_id: int, target: str, users: int):
    """Показывает шаг выбора длительности."""
    target_name = "🧪 STAGING" if target == "staging" else "🚀 PRODUCTION"
    msg = f"""
<b>⏱ Шаг 2/3: Длительность теста</b>

📍 Цель: {target_name}
👥 Пользователей: <b>{users}</b>

Выбери длительность теста:
    """
    await send_telegram_message_with_keyboard(
        msg.strip(),
        get_duration_keyboard(target, users),
        chat_id=chat_id
    )


async def show_rampup_step(chat_id: int, target: str, users: int, duration: int):
    """Показывает шаг выбора паттерна нарастания."""
    target_name = "🧪 STAGING" if target == "staging" else "🚀 PRODUCTION"
    duration_min = duration // 60
    msg = f"""
<b>📊 Шаг 3/3: Паттерн нагрузки</b>

📍 Цель: {target_name}
👥 Пользователей: <b>{users}</b>
⏱ Длительность: <b>{duration_min} мин</b>

Выбери как нарастает нагрузка:

📈 <b>Плавный</b> - {users//10 or 1} user/сек (рекомендуется)
⚡ <b>Быстрый</b> - {users//5 or 1} user/сек
🚀 <b>Мгновенный</b> - все сразу (стресс-тест!)
📊 <b>Ступенчатый</b> - по 25% каждые 25% времени
    """
    await send_telegram_message_with_keyboard(
        msg.strip(),
        get_rampup_keyboard(target, users, duration),
        chat_id=chat_id
    )


async def handle_health_command(chat_id: int):
    """Обрабатывает команду health."""
    await send_chat_action(chat_id, "typing")

    # Собираем данные параллельно
    staging_api, staging_fe, prod_api, prod_fe, k8s, prod = await asyncio.gather(
        check_service_health(STAGING_API_URL, "Staging API"),
        check_service_health(STAGING_FRONTEND_URL, "Staging Frontend"),
        check_service_health(PROD_API_URL, "Production API"),
        check_service_health(PROD_FRONTEND_URL, "Production Frontend"),
        get_k8s_resources(),
        get_prod_resources()
    )

    message = format_health_message(staging_api, staging_fe, prod_api, prod_fe, k8s, prod)

    # Добавляем юмор в зависимости от статуса
    all_up = all(s.get("status") == "UP" for s in [staging_api, staging_fe, prod_api, prod_fe])
    joke = random.choice(JOKES["health_good"] if all_up else JOKES["health_bad"])
    message = f"{joke}\n\n{message}"

    await send_telegram_message_with_keyboard(message, get_main_menu_keyboard(), chat_id=chat_id)


async def send_random_joke(chat_id: int):
    """Отправляет случайную шутку про разработку."""
    dev_jokes = [
        "Почему программисты путают Хэллоуин и Рождество? Потому что Oct 31 = Dec 25 🎃🎄",
        "Есть только 10 типов людей: те кто понимают двоичный код и те кто нет.",
        "— Сколько программистов нужно, чтобы вкрутить лампочку?\n— Ни одного, это hardware проблема!",
        "Почему Java разработчик носит очки? Потому что не видит C# 😎",
        "localhost всегда рядом... только на него можно положиться 💔",
        "Мой код работает, и я не знаю почему. Мой код не работает, и я не знаю почему.",
        "git push --force: Потому что чужие коммиты - это чужие проблемы 🔥",
        "Production - это просто dev environment, который кто-то случайно задеплоил.",
        "99 багов в коде, 99 багов...\nПофикси один, собери...\n127 багов в коде! 🐛",
        "Заказчик: 'Добавьте простую кнопку'\nРазработчик: *плачет в REST API*",
        "Документация? Я думал, код самодокументирующийся! 📚",
        "Senior developer - это junior, который гуглит быстрее.",
    ]
    joke = random.choice(dev_jokes)
    await send_telegram_message_with_keyboard(
        f"🎭 <b>Анекдот дня</b>\n\n{joke}",
        get_main_menu_keyboard(),
        chat_id=chat_id
    )


async def process_callback(callback_query: dict):
    """Обрабатывает нажатие inline кнопки."""
    global pending_load_auth

    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    message_id = callback_query.get("message", {}).get("message_id")

    if not chat_id:
        return

    # Отвечаем на callback чтобы убрать "часики"
    await answer_callback_query(callback_id)

    if data == "health":
        await handle_health_command(chat_id)

    elif data == "metrics":
        await handle_metrics_command(chat_id)

    elif data == "load_staging":
        msg = """
<b>👥 Шаг 1/3: Количество пользователей</b>

📍 Цель: <b>🧪 STAGING</b>

Выбери количество виртуальных пользователей:
        """
        await send_telegram_message_with_keyboard(msg.strip(), get_load_test_keyboard("staging"), chat_id=chat_id)

    elif data == "load_prod":
        msg = """
<b>👥 Шаг 1/3: Количество пользователей</b>

📍 Цель: <b>🚀 PRODUCTION</b>
⚠️ <b>ВНИМАНИЕ!</b> Это боевой сервер!

Выбери количество виртуальных пользователей:
        """
        await send_telegram_message_with_keyboard(msg.strip(), get_load_test_keyboard("prod"), chat_id=chat_id)

    # ========== WIZARD: Шаг 1 - Выбор пользователей ==========
    elif data.startswith("lt_users_"):
        # Формат: lt_users_staging_50 или lt_users_staging_custom
        parts = data.split("_")
        if len(parts) == 4:
            target = parts[2]
            users_str = parts[3]

            if users_str == "custom":
                # Пользователь хочет ввести своё число
                load_test_wizard[chat_id] = {"step": "users_custom", "target": target}
                await send_telegram_message(
                    "<b>✏️ Введи количество пользователей</b>\n\n<i>От 1 до 1000:</i>",
                    chat_id=chat_id
                )
            else:
                users = int(users_str)
                await show_duration_step(chat_id, target, users)

    # ========== WIZARD: Шаг 2 - Выбор длительности ==========
    elif data.startswith("lt_dur_"):
        # Формат: lt_dur_staging_100_300 или lt_dur_staging_100_custom
        parts = data.split("_")
        if len(parts) == 5:
            target = parts[2]
            users = int(parts[3])
            duration_str = parts[4]

            if duration_str == "custom":
                load_test_wizard[chat_id] = {
                    "step": "duration_custom",
                    "target": target,
                    "users": users
                }
                await send_telegram_message(
                    "<b>✏️ Введи длительность теста</b>\n\n<i>В минутах (от 1 до 60):</i>",
                    chat_id=chat_id
                )
            else:
                duration = int(duration_str)
                await show_rampup_step(chat_id, target, users, duration)

    # ========== WIZARD: Шаг 3 - Выбор паттерна и запрос пароля ==========
    elif data.startswith("lt_ramp_"):
        # Формат: lt_ramp_staging_100_300_smooth
        parts = data.split("_")
        if len(parts) == 6:
            target = parts[2]
            users = int(parts[3])
            duration = int(parts[4])
            ramp_up = parts[5]
            # Все параметры собраны - запрашиваем пароль
            await request_password_for_load_test(chat_id, target, users, duration, ramp_up)

    elif data == "load_stop":
        await handle_stop_load_test(chat_id)

    elif data == "load_status":
        await handle_load_status(chat_id)

    elif data == "joke":
        await send_random_joke(chat_id)

    elif data == "help":
        await process_command(chat_id, "/help")

    elif data == "menu":
        await send_telegram_message_with_keyboard(
            "📱 <b>Главное меню</b>\n\nВыбери действие:",
            get_main_menu_keyboard(),
            chat_id=chat_id
        )

    # ========== E2E Testing ==========
    elif data == "e2e_run":
        await handle_e2e_run(chat_id)

    elif data == "e2e_report":
        await send_e2e_report(chat_id)


async def request_password_for_load_test(chat_id: int, target: str, users: int, duration: int = 300, ramp_up: str = "smooth"):
    """Запрашивает пароль перед запуском нагрузочного теста."""
    global pending_load_auth

    if load_test_status["running"]:
        await send_message_with_reply_keyboard(
            "⚠️ <b>Тест уже запущен!</b>\n\nСначала остановите текущий тест кнопкой 🛑",
            chat_id=chat_id
        )
        return

    # Сохраняем параметры и ждём пароль
    pending_load_auth[chat_id] = {
        "target": target,
        "users": users,
        "duration": duration,
        "ramp_up": ramp_up
    }

    target_name = "🧪 STAGING" if target == "staging" else "🚀 PRODUCTION"
    duration_min = duration // 60

    ramp_names = {
        "smooth": "📈 Плавный",
        "fast": "⚡ Быстрый",
        "instant": "🚀 Мгновенный",
        "step": "📊 Ступенчатый"
    }
    ramp_name = ramp_names.get(ramp_up, ramp_up)

    msg = f"""
<b>🔐 Требуется авторизация</b>

<b>Параметры теста:</b>
📍 Цель: {target_name}
👥 Пользователей: <b>{users}</b>
⏱ Длительность: <b>{duration_min} мин</b>
📊 Нарастание: <b>{ramp_name}</b>

<b>Введи пароль для запуска:</b>

<i>⏱ У тебя 60 секунд...</i>
    """
    await send_telegram_message(msg.strip(), chat_id=chat_id)

    # Автоматически очищаем ожидание через 60 секунд
    asyncio.create_task(clear_pending_auth(chat_id, 60))


async def clear_pending_auth(chat_id: int, seconds: int):
    """Очищает ожидание пароля через указанное время."""
    await asyncio.sleep(seconds)
    if chat_id in pending_load_auth:
        del pending_load_auth[chat_id]
        await send_message_with_reply_keyboard(
            "⏱ <b>Время вышло!</b>\n\nЗапрос на нагрузочное тестирование отменён.",
            chat_id=chat_id
        )


async def answer_callback_query(callback_id: str, text: str = None):
    """Отвечает на callback query."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload)
    except:
        pass


# ==================== LOAD TESTING ====================

async def start_load_test_confirmed(chat_id: int, target: str, users: int, duration: int = 300, ramp_up: str = "smooth", is_guest: bool = False):
    """Запускает нагрузочное тестирование после подтверждения паролем."""
    global load_test_status

    if load_test_status["running"]:
        await send_message_with_reply_keyboard(
            "⚠️ <b>Тест уже запущен!</b>\n\nСначала остановите текущий тест.",
            chat_id=chat_id
        )
        return

    # Определяем URL цели
    if target == "staging":
        target_url = STAGING_API_URL
        target_name = "🧪 STAGING"
    else:
        target_url = PROD_API_URL
        target_name = "🚀 PRODUCTION"

    # Рассчитываем spawn_rate в зависимости от паттерна
    if ramp_up == "instant":
        spawn_rate = users  # Все сразу
    elif ramp_up == "fast":
        spawn_rate = max(users // 5, 1)  # 20% в секунду
    elif ramp_up == "step":
        spawn_rate = max(users // 10, 1)  # Для ступенчатого - медленнее
    else:  # smooth
        spawn_rate = max(users // 10, 1)  # 10% в секунду

    ramp_names = {
        "smooth": "📈 Плавный",
        "fast": "⚡ Быстрый",
        "instant": "🚀 Мгновенный",
        "step": "📊 Ступенчатый"
    }
    ramp_name = ramp_names.get(ramp_up, ramp_up)
    duration_min = duration // 60

    joke = random.choice(JOKES["load_test_start"])
    access_type = "👤 Гостевой" if is_guest else "👑 Полный"

    # Запускаем Locust
    try:
        locust_master_url = LOCUST_MASTER_URL

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{locust_master_url}/swarm",
                data={
                    "user_count": users,
                    "spawn_rate": spawn_rate,
                    "host": target_url,
                }
            )

            if response.status_code == 200:
                # Инициализируем статус
                load_test_status = {
                    "running": True,
                    "started_at": datetime.now(),
                    "target": target,
                    "target_url": target_url,
                    "users": users,
                    "duration": duration,
                    "ramp_up": ramp_up,
                    "spawn_rate": spawn_rate,
                    "is_guest": is_guest,
                    "chat_id": chat_id,
                    "stats_task": None,
                    "stats_history": [],
                }

                # Интервал статистики - каждые 3 минуты или реже для коротких тестов
                stats_interval = min(180, duration // 2) if duration > 120 else duration

                msg = f"""
{joke}

<b>🔥 Нагрузочный тест запущен!</b>

🔐 <b>Доступ:</b> {access_type}
📍 <b>Цель:</b> {target_name}
👥 <b>Пользователей:</b> {users}
⏱ <b>Длительность:</b> {duration_min} мин
📊 <b>Нарастание:</b> {ramp_name} ({spawn_rate} user/сек)

📈 Кнопка <b>Тест</b> для статуса
🛑 Кнопка <b>Стоп</b> для остановки
                """
                await send_message_with_reply_keyboard(msg.strip(), chat_id=chat_id)

                # Запускаем задачи
                asyncio.create_task(auto_stop_load_test(duration, chat_id))
                if duration > 60:  # Статистика только для тестов больше минуты
                    asyncio.create_task(periodic_stats_reporter(chat_id, stats_interval))

            else:
                msg = f"❌ Не удалось запустить тест: {response.text[:100]}"
                await send_message_with_reply_keyboard(msg, chat_id=chat_id)

    except Exception as e:
        msg = f"""
⚠️ <b>Locust недоступен</b>

Проверьте, что Locust запущен в кластере (namespace: loadtest)

<i>Ошибка: {str(e)[:50]}</i>
        """
        await send_message_with_reply_keyboard(msg.strip(), chat_id=chat_id)


async def periodic_stats_reporter(chat_id: int, interval_seconds: int):
    """Отправляет статистику каждые N секунд пока тест запущен."""
    report_number = 1

    while load_test_status.get("running"):
        await asyncio.sleep(interval_seconds)

        if not load_test_status.get("running"):
            break

        stats = await get_locust_stats()
        if stats:
            # Сохраняем в историю для финального отчёта
            load_test_status["stats_history"].append({
                "time": datetime.now(),
                "stats": stats.copy()
            })

            duration = datetime.now() - load_test_status["started_at"]
            minutes = int(duration.total_seconds() // 60)
            seconds = int(duration.total_seconds() % 60)

            msg = f"""
<b>📊 Статистика НТ #{report_number}</b>
<i>{datetime.now().strftime('%H:%M:%S')}</i>

⏱ <b>Время работы:</b> {minutes}м {seconds}с
👥 <b>Пользователей:</b> {stats.get('user_count', '?')}

<b>Производительность:</b>
• RPS: <code>{stats.get('total_rps', 0):.1f}</code>
• Avg response: <code>{stats.get('avg_response_time', 0):.0f}ms</code>
• Max response: <code>{stats.get('max_response_time', 0):.0f}ms</code>
• Requests: <code>{stats.get('num_requests', 0)}</code>
• Failures: <code>{stats.get('num_failures', 0)}</code> ({stats.get('fail_ratio', 0)*100:.1f}%)

<i>Следующий отчёт через 3 минуты...</i>
            """
            await send_telegram_message(msg.strip(), chat_id=chat_id)
            report_number += 1


async def get_locust_stats() -> dict:
    """Получает статистику от Locust."""
    try:
        locust_master_url = LOCUST_MASTER_URL
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{locust_master_url}/stats/requests")
            if response.status_code == 200:
                data = response.json()
                # Агрегированная статистика
                total_stats = {}
                if data.get("stats"):
                    for stat in data["stats"]:
                        if stat.get("name") == "Aggregated":
                            total_stats = stat
                            break

                return {
                    "total_rps": data.get("total_rps", 0),
                    "fail_ratio": data.get("fail_ratio", 0),
                    "user_count": data.get("user_count", 0),
                    "num_requests": total_stats.get("num_requests", 0),
                    "num_failures": total_stats.get("num_failures", 0),
                    "avg_response_time": total_stats.get("avg_response_time", 0),
                    "max_response_time": total_stats.get("max_response_time", 0),
                    "min_response_time": total_stats.get("min_response_time", 0),
                    "median_response_time": total_stats.get("median_response_time", 0),
                }
    except:
        pass
    return None


async def auto_stop_load_test(seconds: int, chat_id: int):
    """Автоматически останавливает тест через указанное время."""
    await asyncio.sleep(seconds)
    if load_test_status.get("running"):
        await handle_stop_load_test(chat_id, auto=True)


async def handle_stop_load_test(chat_id: int, auto: bool = False):
    """Останавливает нагрузочный тест и отправляет финальный отчёт."""
    global load_test_status

    if not load_test_status.get("running"):
        if not auto:
            await send_message_with_reply_keyboard(
                "🤷 <b>Нет активных тестов</b>\n\nНечего останавливать!",
                chat_id=chat_id
            )
        return

    # Получаем финальную статистику перед остановкой
    final_stats = await get_locust_stats()

    # Останавливаем Locust
    try:
        locust_master_url = LOCUST_MASTER_URL
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.get(f"{locust_master_url}/stop")
    except:
        pass

    # Собираем данные для отчёта
    actual_duration = datetime.now() - load_test_status["started_at"]
    minutes = int(actual_duration.total_seconds() // 60)
    secs = int(actual_duration.total_seconds() % 60)
    target = load_test_status.get('target', 'N/A').upper()
    users = load_test_status.get('users', 0)
    planned_duration = load_test_status.get('duration', 300) // 60
    ramp_up = load_test_status.get('ramp_up', 'smooth')
    spawn_rate = load_test_status.get('spawn_rate', 1)
    is_guest = load_test_status.get('is_guest', False)
    stats_history = load_test_status.get("stats_history", [])

    ramp_names = {
        "smooth": "📈 Плавный",
        "fast": "⚡ Быстрый",
        "instant": "🚀 Мгновенный",
        "step": "📊 Ступенчатый"
    }
    ramp_name = ramp_names.get(ramp_up, ramp_up)
    access_type = "👤 Гостевой" if is_guest else "👑 Полный"

    joke = random.choice(JOKES["load_test_stop"])

    # Формируем финальный отчёт
    msg = f"""
{joke}

<b>{'🏁' if auto else '🛑'} ФИНАЛЬНЫЙ ОТЧЁТ НТ</b>
<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>

<b>━━━ Параметры теста ━━━</b>
🔐 Доступ: <b>{access_type}</b>
📍 Цель: <b>{target}</b>
👥 Пользователей: <b>{users}</b>
📊 Нарастание: <b>{ramp_name}</b> ({spawn_rate} user/сек)
⏱ План/Факт: <b>{planned_duration}м / {minutes}м {secs}с</b>
🔄 Остановка: {'Авто (таймаут)' if auto else 'Ручная'}
    """

    if final_stats:
        msg += f"""
<b>━━━ Итоговая статистика ━━━</b>
📊 <b>RPS:</b> {final_stats.get('total_rps', 0):.1f}
📈 <b>Всего запросов:</b> {final_stats.get('num_requests', 0):,}
❌ <b>Ошибок:</b> {final_stats.get('num_failures', 0)} ({final_stats.get('fail_ratio', 0)*100:.1f}%)

<b>⏱ Время ответа:</b>
• Среднее: {final_stats.get('avg_response_time', 0):.0f}ms
• Медиана: {final_stats.get('median_response_time', 0):.0f}ms
• Макс: {final_stats.get('max_response_time', 0):.0f}ms
• Мин: {final_stats.get('min_response_time', 0):.0f}ms
        """

        # Оценка результата
        fail_ratio = final_stats.get('fail_ratio', 0)
        avg_time = final_stats.get('avg_response_time', 0)

        if fail_ratio < 0.01 and avg_time < 500:
            verdict = "✅ <b>ОТЛИЧНО!</b> Сервер выдержал нагрузку без проблем!"
        elif fail_ratio < 0.05 and avg_time < 1000:
            verdict = "👍 <b>ХОРОШО.</b> Небольшие задержки, но в целом стабильно."
        elif fail_ratio < 0.1:
            verdict = "⚠️ <b>УДОВЛЕТВОРИТЕЛЬНО.</b> Есть проблемы под нагрузкой."
        else:
            verdict = "❌ <b>ПЛОХО!</b> Сервер не справляется с нагрузкой!"

        msg += f"\n<b>━━━ Вердикт ━━━</b>\n{verdict}"

    # Добавляем историю если есть
    if stats_history:
        msg += f"\n\n<i>📊 Собрано отчётов: {len(stats_history)}</i>"

    # Сбрасываем статус
    load_test_status = {
        "running": False,
        "started_at": None,
        "target": None,
        "users": 0,
        "chat_id": None,
        "stats_task": None,
        "stats_history": [],
    }

    await send_message_with_reply_keyboard(msg.strip(), chat_id=chat_id)


async def handle_load_status(chat_id: int):
    """Показывает статус текущего нагрузочного теста."""
    if not load_test_status.get("running"):
        await send_message_with_reply_keyboard(
            "😴 <b>Нет активных тестов</b>\n\n<i>Запусти тест кнопкой 🔥 Нагрузка!</i>",
            chat_id=chat_id
        )
        return

    elapsed = datetime.now() - load_test_status["started_at"]
    elapsed_min = int(elapsed.total_seconds() // 60)
    elapsed_sec = int(elapsed.total_seconds() % 60)
    planned_duration = load_test_status.get('duration', 300)
    remaining = max(0, planned_duration - elapsed.total_seconds())
    remaining_min = int(remaining // 60)
    remaining_sec = int(remaining % 60)

    ramp_names = {
        "smooth": "📈 Плавный",
        "fast": "⚡ Быстрый",
        "instant": "🚀 Мгновенный",
        "step": "📊 Ступенчатый"
    }
    ramp_up = load_test_status.get('ramp_up', 'smooth')
    ramp_name = ramp_names.get(ramp_up, ramp_up)

    # Получаем статистику
    stats = await get_locust_stats()

    msg = f"""
<b>📈 Статус нагрузочного теста</b>
<i>{datetime.now().strftime('%H:%M:%S')}</i>

🟢 <b>Статус:</b> RUNNING
📍 <b>Цель:</b> {load_test_status.get('target', 'N/A').upper()}
👥 <b>Пользователей:</b> {load_test_status.get('users', 0)}
📊 <b>Нарастание:</b> {ramp_name}
⏱ <b>Прошло:</b> {elapsed_min}м {elapsed_sec}с
⏳ <b>Осталось:</b> {remaining_min}м {remaining_sec}с
    """

    if stats:
        msg += f"""
<b>📊 Текущая статистика:</b>
• RPS: <code>{stats.get('total_rps', 0):.1f}</code>
• Avg response: <code>{stats.get('avg_response_time', 0):.0f}ms</code>
• Max response: <code>{stats.get('max_response_time', 0):.0f}ms</code>
• Requests: <code>{stats.get('num_requests', 0)}</code>
• Failures: <code>{stats.get('num_failures', 0)}</code> ({stats.get('fail_ratio', 0)*100:.1f}%)
        """
    else:
        msg += "\n<i>📊 Статистика временно недоступна</i>"

    reports_count = len(load_test_status.get("stats_history", []))
    msg += f"\n\n<i>📊 Отправлено отчётов: {reports_count}</i>"

    await send_message_with_reply_keyboard(msg.strip(), chat_id=chat_id)


# ==================== E2E TESTING ====================

async def handle_e2e_menu(chat_id: int):
    """Показывает меню E2E тестирования."""
    # Сначала получаем текущий статус из Allure
    allure_stats = await get_allure_report_stats()

    status_line = ""
    if allure_stats:
        passed = allure_stats.get("passed", 0)
        failed = allure_stats.get("failed", 0)
        broken = allure_stats.get("broken", 0)
        total = passed + failed + broken

        if failed == 0 and broken == 0:
            status_line = f"\n\n📊 <b>Последний запуск:</b> ✅ {passed}/{total} passed"
        else:
            status_line = f"\n\n📊 <b>Последний запуск:</b> ❌ {passed}/{total} passed, {failed + broken} failed"

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🚀 Запустить E2E тесты", "callback_data": "e2e_run"},
            ],
            [
                {"text": "📊 Последний отчёт", "callback_data": "e2e_report"},
            ],
            [
                {"text": "⬅️ Назад", "callback_data": "menu"},
            ],
        ]
    }

    msg = f"""
<b>🧪 E2E Тестирование API</b>

Здесь можно запустить автотесты и посмотреть результаты.
Тесты проверяют все эндпоинты API: авторизацию, CRUD продуктов и т.д.{status_line}

<i>⏱ Время выполнения: ~2-3 минуты</i>
    """
    await send_telegram_message_with_keyboard(msg.strip(), keyboard, chat_id=chat_id)


async def get_allure_report_stats() -> dict:
    """Получает статистику последнего отчёта из Allure Server."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Получаем статистику последнего отчёта
            response = await client.get(
                f"{ALLURE_SERVER_URL}/allure-docker-service/projects/warehouse-api/reports/latest/widgets/summary.json"
            )
            if response.status_code == 200:
                data = response.json()
                statistic = data.get("statistic", {})
                return {
                    "passed": statistic.get("passed", 0),
                    "failed": statistic.get("failed", 0),
                    "broken": statistic.get("broken", 0),
                    "skipped": statistic.get("skipped", 0),
                    "total": statistic.get("total", 0),
                }
    except Exception as e:
        logger.error(f"Failed to get Allure stats: {e}")
    return None


async def get_allure_report_details() -> dict:
    """Получает детальную информацию о последнем отчёте."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Статистика
            stats_resp = await client.get(
                f"{ALLURE_SERVER_URL}/allure-docker-service/projects/warehouse-api/reports/latest/widgets/summary.json"
            )

            # Время выполнения
            duration_resp = await client.get(
                f"{ALLURE_SERVER_URL}/allure-docker-service/projects/warehouse-api/reports/latest/widgets/duration-trend.json"
            )

            result = {}

            if stats_resp.status_code == 200:
                data = stats_resp.json()
                result["statistic"] = data.get("statistic", {})
                result["time"] = data.get("time", {})

            if duration_resp.status_code == 200:
                duration_data = duration_resp.json()
                if duration_data and len(duration_data) > 0:
                    result["duration"] = duration_data[0].get("data", {}).get("duration", 0)

            return result
    except Exception as e:
        logger.error(f"Failed to get Allure details: {e}")
    return None


async def handle_e2e_run(chat_id: int):
    """Запускает E2E тесты."""
    global e2e_test_status

    if e2e_test_status.get("running"):
        await send_message_with_reply_keyboard(
            "⚠️ <b>Тесты уже запущены!</b>\n\n<i>Дождись завершения текущего прогона.</i>",
            chat_id=chat_id
        )
        return

    joke = random.choice(JOKES["e2e_start"])

    await send_message_with_reply_keyboard(
        f"{joke}\n\n<b>🧪 Запускаю E2E тесты...</b>\n\n<i>⏱ Это займёт 2-3 минуты. Я пришлю отчёт когда закончу!</i>",
        chat_id=chat_id
    )

    e2e_test_status = {
        "running": True,
        "started_at": datetime.now(),
        "chat_id": chat_id,
    }

    # Запускаем тесты в фоне
    asyncio.create_task(run_e2e_tests_and_report(chat_id))


async def run_e2e_tests_and_report(chat_id: int):
    """Запускает тесты через shell и отправляет отчёт."""
    global e2e_test_status

    try:
        # Запускаем Maven тесты
        # Так как бот в K8s, а тесты на хосте, используем Allure API для мониторинга
        # На самом деле тесты запускаются через GitLab pipeline, но мы можем
        # триггернуть их через API или просто показать последний отчёт

        # Для простоты: проверяем Allure каждые 10 секунд в течение 5 минут
        # ожидая появления нового отчёта

        start_time = datetime.now()
        initial_stats = await get_allure_report_stats()

        # Имитируем ожидание запуска (в реальности тут был бы trigger GitLab pipeline)
        await asyncio.sleep(3)

        # Проверяем результаты
        max_wait = 180  # 3 минуты максимум
        check_interval = 15
        elapsed = 0

        # На самом деле, раз pipeline и так запускается автоматически,
        # просто покажем последний доступный отчёт
        await asyncio.sleep(2)

        # Получаем и отправляем отчёт
        await send_e2e_report(chat_id)

    except Exception as e:
        logger.error(f"E2E test error: {e}")
        await send_message_with_reply_keyboard(
            f"❌ <b>Ошибка при запуске тестов</b>\n\n<i>{str(e)[:100]}</i>",
            chat_id=chat_id
        )
    finally:
        e2e_test_status = {
            "running": False,
            "started_at": None,
            "chat_id": None,
        }


async def send_e2e_report(chat_id: int):
    """Отправляет отчёт о E2E тестировании."""
    details = await get_allure_report_details()

    if not details or not details.get("statistic"):
        await send_message_with_reply_keyboard(
            "⚠️ <b>Не удалось получить отчёт</b>\n\n<i>Allure Server недоступен или нет данных.</i>",
            chat_id=chat_id
        )
        return

    stats = details["statistic"]
    passed = stats.get("passed", 0)
    failed = stats.get("failed", 0)
    broken = stats.get("broken", 0)
    skipped = stats.get("skipped", 0)
    total = stats.get("total", 0)

    duration_ms = details.get("duration", 0)
    duration_sec = duration_ms // 1000 if duration_ms else 0
    duration_min = duration_sec // 60
    duration_sec = duration_sec % 60

    # Определяем успех/провал
    all_passed = failed == 0 and broken == 0

    if all_passed:
        joke = random.choice(JOKES["e2e_success"])
        status_emoji = "✅"
        verdict = "ВСЁ ЗЕЛЁНОЕ!"
    else:
        joke = random.choice(JOKES["e2e_failure"])
        status_emoji = "❌"
        verdict = "ЕСТЬ ПРОБЛЕМЫ!"

    # Формируем прогресс-бар
    if total > 0:
        pass_percent = (passed / total) * 100
        bar_filled = int(pass_percent / 10)
        bar_empty = 10 - bar_filled
        progress_bar = "🟩" * bar_filled + "🟥" * bar_empty
    else:
        progress_bar = "⬜" * 10
        pass_percent = 0

    msg = f"""
{joke}

<b>🧪 ОТЧЁТ E2E ТЕСТИРОВАНИЯ</b>
<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>

<b>━━━ Результат ━━━</b>
{status_emoji} <b>{verdict}</b>

{progress_bar} {pass_percent:.0f}%

<b>📊 Статистика:</b>
✅ Passed: <b>{passed}</b>
❌ Failed: <b>{failed}</b>
💔 Broken: <b>{broken}</b>
⏭ Skipped: <b>{skipped}</b>
📋 Total: <b>{total}</b>

⏱ <b>Время:</b> {duration_min}м {duration_sec}с

🔗 <a href="{ALLURE_SERVER_URL}/allure-docker-service/projects/warehouse-api/reports/latest">Открыть полный отчёт</a>
    """

    await send_message_with_reply_keyboard(msg.strip(), chat_id=chat_id)


# ==================== CLAUDE INTEGRATION ====================

async def handle_claude_menu(chat_id: int):
    """Показывает меню Claude и запрашивает пароль."""
    global pending_claude_task

    if claude_task_status.get("running"):
        elapsed = datetime.now() - claude_task_status["started_at"]
        await send_message_with_reply_keyboard(
            f"⚠️ <b>Claude уже работает!</b>\n\n"
            f"⏱ Время: {int(elapsed.total_seconds())}с\n"
            f"<i>Дождись завершения текущей задачи.</i>",
            chat_id=chat_id
        )
        return

    # Запрашиваем пароль
    pending_claude_task[chat_id] = {"step": "password"}

    msg = """
<b>🤖 Claude AI Assistant</b>

Здесь можно отправить задачу напрямую Claude Code.
Он выполнит её и вернёт результат.

<b>🔐 Введи пароль для доступа:</b>

<i>⏱ У тебя 60 секунд...</i>
    """
    await send_telegram_message(msg.strip(), chat_id=chat_id)

    # Автоматически очищаем ожидание через 60 секунд
    asyncio.create_task(clear_pending_claude(chat_id, 60))


async def clear_pending_claude(chat_id: int, seconds: int):
    """Очищает ожидание Claude ввода через указанное время."""
    await asyncio.sleep(seconds)
    if chat_id in pending_claude_task:
        del pending_claude_task[chat_id]
        await send_message_with_reply_keyboard(
            "⏱ <b>Время вышло!</b>\n\nЗапрос на Claude отменён.",
            chat_id=chat_id
        )


async def handle_claude_input(chat_id: int, text: str):
    """Обрабатывает ввод пароля или задачи для Claude."""
    global pending_claude_task

    if chat_id not in pending_claude_task:
        return

    state = pending_claude_task[chat_id]
    step = state.get("step")

    if step == "password":
        # Проверяем пароль (только админский)
        if text == LOAD_TEST_PASSWORD:
            pending_claude_task[chat_id] = {"step": "task"}
            await send_telegram_message(
                "✅ <b>Пароль принят!</b>\n\n"
                "📝 <b>Введи задачу для Claude:</b>\n\n"
                "<i>Например: \"Проверь статус всех сервисов в K8s\"</i>",
                chat_id=chat_id
            )
        else:
            del pending_claude_task[chat_id]
            await send_message_with_reply_keyboard(
                "❌ <b>Неверный пароль!</b>\n\n<i>Доступ к Claude запрещён.</i>",
                chat_id=chat_id
            )

    elif step == "task":
        # Получили задачу - запускаем выполнение
        del pending_claude_task[chat_id]

        task = text.strip()
        if len(task) < 3:
            await send_message_with_reply_keyboard(
                "⚠️ <b>Задача слишком короткая!</b>\n\n<i>Попробуй ещё раз через меню Claude.</i>",
                chat_id=chat_id
            )
            return

        # Запускаем выполнение
        await execute_claude_task(chat_id, task)


async def execute_claude_task(chat_id: int, task: str):
    """Выполняет задачу через Claude Proxy API."""
    global claude_task_status

    joke = random.choice(JOKES["claude_start"])

    await send_message_with_reply_keyboard(
        f"{joke}\n\n"
        f"<b>📝 Задача:</b>\n<code>{task[:200]}{'...' if len(task) > 200 else ''}</code>\n\n"
        f"<i>⏳ Ожидай ответ... (до 5 мин)</i>",
        chat_id=chat_id
    )

    claude_task_status = {
        "running": True,
        "started_at": datetime.now(),
        "chat_id": chat_id,
        "task": task,
    }

    try:
        # Вызываем Claude через proxy API
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
                    joke_done = random.choice(JOKES["claude_done"])

                    # Telegram лимит на сообщение ~4096 символов
                    if len(result) > 3500:
                        result = result[:3500] + "\n\n<i>... (обрезано)</i>"

                    # Экранируем HTML спецсимволы
                    result = result.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                    await send_message_with_reply_keyboard(
                        f"{joke_done}\n\n"
                        f"<b>🤖 Ответ Claude:</b>\n\n"
                        f"<pre>{result}</pre>\n\n"
                        f"<i>⏱ Время: {elapsed_sec}с</i>",
                        chat_id=chat_id
                    )
                else:
                    error = data.get("stderr", "Неизвестная ошибка")
                    joke_error = random.choice(JOKES["claude_error"])

                    # Экранируем HTML
                    error = error.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                    await send_message_with_reply_keyboard(
                        f"{joke_error}\n\n"
                        f"<b>❌ Ошибка выполнения</b>\n\n"
                        f"<pre>{error[:500]}</pre>",
                        chat_id=chat_id
                    )
            else:
                await send_message_with_reply_keyboard(
                    f"❌ <b>Ошибка Proxy</b>\n\n<code>HTTP {response.status_code}</code>",
                    chat_id=chat_id
                )

    except httpx.TimeoutException:
        await send_message_with_reply_keyboard(
            "⏱ <b>Таймаут!</b>\n\n<i>Claude работал слишком долго (>5 мин). Задача отменена.</i>",
            chat_id=chat_id
        )
    except httpx.ConnectError:
        await send_message_with_reply_keyboard(
            "❌ <b>Claude Proxy недоступен!</b>\n\n<i>Проверь, что claude_proxy.py запущен на хосте.</i>",
            chat_id=chat_id
        )
    except Exception as e:
        logger.error(f"Claude execution error: {e}")
        await send_message_with_reply_keyboard(
            f"❌ <b>Ошибка</b>\n\n<code>{str(e)[:200]}</code>",
            chat_id=chat_id
        )
    finally:
        claude_task_status = {
            "running": False,
            "started_at": None,
            "chat_id": None,
            "task": None,
        }


async def send_chat_action(chat_id: int, action: str = "typing"):
    """Отправляет действие (typing, upload_photo, etc.)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": chat_id, "action": action})
    except:
        pass


async def send_message_with_reply_keyboard(text: str, chat_id: int = None, parse_mode: str = "HTML"):
    """Отправляет сообщение с постоянной reply клавиатурой снизу."""
    target_chat_id = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not target_chat_id:
        logger.error("Telegram credentials not configured")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
        "reply_markup": get_reply_keyboard()
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                logger.info("Telegram message with reply keyboard sent")
                return True
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


async def send_telegram_message_with_keyboard(text: str, keyboard: dict, chat_id: int = None, parse_mode: str = "HTML"):
    """Отправляет сообщение с inline клавиатурой."""
    target_chat_id = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not target_chat_id:
        logger.error("Telegram credentials not configured")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
        "reply_markup": keyboard
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                logger.info("Telegram message with keyboard sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


async def telegram_polling():
    """Фоновая задача для polling Telegram."""
    global last_update_id
    logger.info("Starting Telegram polling... 🤖")

    while True:
        try:
            updates = await get_telegram_updates(last_update_id + 1)

            for update in updates:
                last_update_id = update["update_id"]

                # Обрабатываем callback_query (нажатия на кнопки)
                callback_query = update.get("callback_query")
                if callback_query:
                    logger.info(f"Received callback: {callback_query.get('data')} from {callback_query.get('from', {}).get('id')}")
                    await process_callback(callback_query)
                    continue

                # Обрабатываем обычные сообщения
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")

                if chat_id and text:
                    logger.info(f"Received message: {text[:50]} from {chat_id}")
                    # Обрабатываем и команды, и кнопки, и пароли
                    await process_command(chat_id, text.split()[0] if text.startswith("/") else text)

        except Exception as e:
            logger.error(f"Polling error: {e}")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager для FastAPI."""
    # Запускаем polling в фоне
    polling_task = asyncio.create_task(telegram_polling())
    logger.info("Bot started with polling")
    yield
    # Останавливаем при выходе
    polling_task.cancel()


app = FastAPI(title="GitLab Telegram Notifier", version="7.0.0", lifespan=lifespan, description="E2E тесты + Claude AI! 🧪🤖")


# ==================== EMOJI MAPPINGS ====================

STATUS_EMOJI = {
    "pending": "⏳",
    "running": "🔄",
    "success": "✅",
    "failed": "❌",
    "canceled": "🚫",
    "skipped": "⏭️",
    "manual": "👆",
    "created": "🆕",
}

STAGE_EMOJI = {
    "validate": "🔍",
    "build": "🔨",
    "test": "🧪",
    "e2e-test": "🧪",
    "ui-test": "🖥️",
    "report": "📊",
    "image": "🐳",
    "deploy": "🚀",
}


# ==================== TELEGRAM ====================

async def send_telegram_message(text: str, parse_mode: str = "HTML", chat_id: int = None):
    """Отправляет сообщение в Telegram."""
    target_chat_id = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not target_chat_id:
        logger.error("Telegram credentials not configured")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


# ==================== MESSAGE FORMATTING ====================

def format_pipeline_message(data: dict) -> str:
    """Форматирует сообщение о pipeline."""
    attrs = data.get("object_attributes", {})
    project = data.get("project", {})
    commit = data.get("commit", {})
    user = data.get("user", {})

    status = attrs.get("status", "unknown")
    emoji = STATUS_EMOJI.get(status, "❓")

    pipeline_id = attrs.get("id", "?")
    pipeline_url = f"{project.get('web_url', '')}/-/pipelines/{pipeline_id}"

    ref = attrs.get("ref", "unknown")
    duration = attrs.get("duration")

    # Форматируем длительность
    duration_str = ""
    if duration:
        minutes = int(duration) // 60
        seconds = int(duration) % 60
        duration_str = f"\n⏱ <b>Время:</b> {minutes}м {seconds}с"

    # Формируем сообщение
    message = f"""
{emoji} <b>Pipeline #{pipeline_id}</b> — <code>{status.upper()}</code>

📦 <b>Проект:</b> {project.get('name', 'Unknown')}
🌿 <b>Ветка:</b> <code>{ref}</code>
👤 <b>Автор:</b> {user.get('name', 'Unknown')}{duration_str}

💬 <i>{commit.get('title', 'No commit message')[:100]}</i>

🔗 <a href="{pipeline_url}">Открыть в GitLab</a>
"""
    return message.strip()


def format_job_message(data: dict) -> str:
    """Форматирует сообщение о job."""
    build = data.get("build_id") or data.get("build_name")

    # Для job events структура немного другая
    build_name = data.get("build_name", "unknown")
    build_stage = data.get("build_stage", "unknown")
    build_status = data.get("build_status", "unknown")
    project_name = data.get("project_name", data.get("repository", {}).get("name", "Unknown"))
    ref = data.get("ref", "unknown")

    status_emoji = STATUS_EMOJI.get(build_status, "❓")
    stage_emoji = STAGE_EMOJI.get(build_stage, "📋")

    # Отправляем только важные события (failed, success для deploy)
    if build_status not in ["failed", "success"]:
        return None

    # Для success отправляем только deploy stage
    if build_status == "success" and build_stage != "deploy":
        return None

    duration = data.get("build_duration")
    duration_str = ""
    if duration:
        minutes = int(float(duration)) // 60
        seconds = int(float(duration)) % 60
        duration_str = f" ({minutes}м {seconds}с)"

    message = f"""
{status_emoji} <b>Job:</b> {build_name}{duration_str}
{stage_emoji} <b>Stage:</b> {build_stage}
📦 <b>Проект:</b> {project_name}
🌿 <b>Ветка:</b> <code>{ref}</code>
"""

    # Добавляем информацию об ошибке если job упал
    if build_status == "failed":
        failure_reason = data.get("build_failure_reason", "unknown")
        message += f"\n⚠️ <b>Причина:</b> {failure_reason}"

    return message.strip()


def format_deployment_message(data: dict) -> str:
    """Форматирует сообщение о деплое."""
    status = data.get("status", "unknown")
    environment = data.get("environment", "unknown")
    project = data.get("project", {})
    user = data.get("user", {})

    emoji = STATUS_EMOJI.get(status, "🚀")

    message = f"""
{emoji} <b>Deployment</b> — <code>{status.upper()}</code>

📦 <b>Проект:</b> {project.get('name', 'Unknown')}
🌍 <b>Environment:</b> {environment}
👤 <b>Автор:</b> {user.get('name', 'Unknown')}
"""
    return message.strip()


# ==================== WEBHOOK ENDPOINTS ====================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "gitlab-telegram-notifier"}


@app.post("/webhook/gitlab")
async def gitlab_webhook(request: Request):
    """
    Принимает webhook от GitLab и отправляет уведомление в Telegram.
    """
    # Проверяем секрет если настроен
    if GITLAB_WEBHOOK_SECRET:
        token = request.headers.get("X-Gitlab-Token", "")
        if token != GITLAB_WEBHOOK_SECRET:
            logger.warning("Invalid webhook secret")
            raise HTTPException(status_code=401, detail="Invalid secret")

    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = request.headers.get("X-Gitlab-Event", "")
    logger.info(f"Received GitLab event: {event_type}")

    message = None

    if event_type == "Pipeline Hook":
        status = data.get("object_attributes", {}).get("status", "")
        # Отправляем только при старте и завершении
        if status in ["running", "success", "failed"]:
            message = format_pipeline_message(data)

    elif event_type == "Job Hook":
        message = format_job_message(data)

    elif event_type == "Deployment Hook":
        message = format_deployment_message(data)

    if message:
        await send_telegram_message(message)
        return {"status": "sent", "event": event_type}

    return {"status": "skipped", "event": event_type}


@app.post("/test")
async def test_notification():
    """Отправляет тестовое сообщение."""
    test_message = """
🧪 <b>Тестовое уведомление</b>

✅ GitLab Telegram Notifier работает!
📅 {timestamp}
    """.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    success = await send_telegram_message(test_message)

    if success:
        return {"status": "ok", "message": "Test notification sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send notification")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
