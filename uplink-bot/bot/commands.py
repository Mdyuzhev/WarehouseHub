"""
Command handlers for Uplink bot.
Processes /commands from Matrix users via botservice webhook.
"""

import logging
from bot import uplink
from bot.messages import format_health_message
from services import check_all_health, get_k8s_resources, robot_service

logger = logging.getLogger(__name__)


HELP_TEXT = """<b>🤖 Warehouse Uplink Bot</b>

<b>Команды:</b>
/status — статус серверов
/pods — сервисы (docker-compose)
/metrics — CPU / RAM
/robot — статус робота
/help — эта справка"""


async def handle_command(text: str) -> bool:
    """Route and execute a command. Returns True if handled."""
    text = text.strip()
    cmd = text.split()[0].lower() if text else ""

    handlers = {
        "/help": cmd_help,
        "/start": cmd_help,
        "/status": cmd_status,
        "/pods": cmd_pods,
        "/metrics": cmd_metrics,
        "/robot": cmd_robot,
    }

    handler = handlers.get(cmd)
    if handler:
        await handler()
        return True
    return False


async def cmd_help():
    await uplink.send_message(text="Warehouse Uplink Bot — /help", html=HELP_TEXT)


async def cmd_status():
    health_data = await check_all_health()
    plain, html = format_health_message(health_data)
    await uplink.send_message(text=plain, html=html)


async def cmd_pods():
    k8s = await get_k8s_resources()

    html = "<b>📦 Сервисы Homelab</b><br/><br/>"
    if k8s.get("pods"):
        for pod in k8s["pods"]:
            if pod["status"] == "Running":
                icon = "🟢"
            elif pod["status"] == "Error":
                icon = "🔴"
            else:
                icon = "🟡"
            restarts = f" (↻{pod['restarts']})" if pod.get('restarts') and pod['restarts'] != "0" else ""
            html += f"{icon} <code>{pod['name']}</code>{restarts}<br/>"
    else:
        html += "<i>Не удалось получить информацию о сервисах</i>"

    await uplink.send_message(text="Сервисы Homelab", html=html.strip())


async def cmd_metrics():
    k8s = await get_k8s_resources()

    html = "<b>📊 Метрики Homelab</b><br/><br/>"
    if k8s.get("node"):
        html += f"💻 CPU: {k8s['node'].get('cpu_percent', 'N/A')}<br/>"
        html += f"💾 RAM: {k8s['node'].get('memory_percent', 'N/A')}"
    else:
        html += "<i>Метрики временно недоступны</i>"

    await uplink.send_message(text="Метрики Homelab", html=html)


async def cmd_robot():
    status = robot_service.get_status()
    if status is None:
        html = "<b>🤖 Robot</b><br/><br/><i>Robot API недоступен</i>"
        await uplink.send_message(text="Robot — недоступен", html=html)
        return

    is_running = status.get("running", False)
    scenario = status.get("scenario", "—")
    icon = "🟢" if is_running else "⚪"

    html = f"<b>🤖 Robot</b><br/><br/>"
    html += f"{icon} Статус: {'запущен' if is_running else 'остановлен'}<br/>"
    if is_running:
        html += f"📋 Сценарий: {scenario}<br/>"
        if status.get("operations_done") is not None:
            html += f"📊 Операций: {status['operations_done']}"

    plain = f"Robot — {'запущен ({scenario})' if is_running else 'остановлен'}"
    await uplink.send_message(text=plain, html=html.strip())
