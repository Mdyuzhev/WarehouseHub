"""
Command handlers for Uplink bot.
Processes /wh commands from Matrix users via WS bridge.
"""

import logging
from bot import uplink
from bot.messages import format_health_message
from services import check_all_health, get_k8s_resources, robot_service

logger = logging.getLogger(__name__)

SCENARIOS = {"receiving", "shipping", "inventory"}
SCENARIO_NAMES = {
    "receiving": "Приёмка",
    "shipping": "Отгрузка",
    "inventory": "Инвентаризация",
}


# =============================================================================
# WS bridge handler (returns plain text for Matrix)
# =============================================================================

async def handle_command_text(cmd: str, args: list = None) -> str:
    """Process command and return result as text (for WS bridge)."""
    args = args or []
    cmd = cmd.strip().lower()

    handlers = {
        "/help": lambda: get_help_text(),
        "/start": lambda: get_help_text(),
        "/status": lambda: get_status_text(),
        "/pods": lambda: get_pods_text(),
        "/metrics": lambda: get_metrics_text(),
        "/robot": lambda: get_robot_text(args),
        "/poll": lambda: get_status_text(),
    }

    handler = handlers.get(cmd)
    if handler:
        return await handler()
    return f"Unknown command: {cmd}. Use /wh help."


async def get_help_text() -> str:
    return (
        "🤖 WarehouseHub Bot\n\n"
        "/wh status — статус серверов\n"
        "/wh pods — сервисы\n"
        "/wh metrics — CPU / RAM\n"
        "/wh robot — статус робота\n"
        "/wh robot start <scenario> — запуск (receiving/shipping/inventory)\n"
        "/wh robot stop — остановка\n"
        "/wh robot stats — статистика\n"
        "/wh help — справка"
    )


async def get_status_text() -> str:
    health_data = await check_all_health()
    lines = ["🏥 Статус:"]
    for key in ("staging_api", "staging_fe"):
        svc = health_data.get(key, {})
        icon = "🟢" if svc.get("status") == "UP" else "🔴"
        name = svc.get("name", key)
        latency = f" ({svc.get('latency_ms', '?')}ms)" if svc.get("latency_ms") else ""
        lines.append(f"{icon} {name}{latency}")
    return "\n".join(lines)


async def get_pods_text() -> str:
    k8s = await get_k8s_resources()
    lines = ["📦 Сервисы:"]
    for pod in k8s.get("pods", []):
        if pod["status"] == "Running":
            icon = "🟢"
        elif pod["status"] == "Error":
            icon = "🔴"
        else:
            icon = "🟡"
        restarts = f" (↻{pod['restarts']})" if pod.get("restarts") and pod["restarts"] != "0" else ""
        lines.append(f"{icon} {pod['name']}{restarts}")
    return "\n".join(lines) if len(lines) > 1 else "No service data"


async def get_metrics_text() -> str:
    k8s = await get_k8s_resources()
    node = k8s.get("node", {})
    if node:
        return f"📊 Метрики:\nCPU: {node.get('cpu_percent', 'N/A')}\nRAM: {node.get('memory_percent', 'N/A')}"
    return "Метрики недоступны"


async def get_robot_text(args: list = None) -> str:
    """Handle /wh robot [subcommand] [args]."""
    args = args or []
    sub = args[0].lower() if args else ""

    if sub == "start":
        return await robot_start(args[1:])
    elif sub == "stop":
        return await robot_stop()
    elif sub == "stats":
        return await robot_stats()
    else:
        return await robot_status()


async def robot_status() -> str:
    status = robot_service.get_status()
    if status is None:
        return "🤖 Robot — API недоступен"

    is_running = status.get("running", False)
    scenario = status.get("scenario", "—")
    icon = "🟢" if is_running else "⚪"
    result = f"🤖 Robot: {icon} {'запущен' if is_running else 'остановлен'}"
    if is_running:
        result += f"\n📋 Сценарий: {SCENARIO_NAMES.get(scenario, scenario)}"
        if status.get("operations_done") is not None:
            result += f"\n📊 Операций: {status['operations_done']}"
    return result


async def robot_start(args: list) -> str:
    if not args:
        scenarios = ", ".join(SCENARIOS)
        return f"Укажите сценарий: /wh robot start <{scenarios}>"

    scenario = args[0].lower()
    if scenario not in SCENARIOS:
        return f"❌ Неизвестный сценарий: {scenario}\nДоступные: {', '.join(SCENARIOS)}"

    # Check if already running
    status = robot_service.get_status()
    if status and status.get("running"):
        return f"⚠️ Robot уже запущен ({status.get('scenario')}). Сначала /wh robot stop"

    speed = args[1] if len(args) > 1 and args[1] in ("slow", "normal", "fast") else "normal"
    result = robot_service.start_scenario(scenario, speed=speed, environment="home")

    if result and result.get("status") == "started":
        name = SCENARIO_NAMES.get(scenario, scenario)
        return f"🚀 Robot запущен!\n📋 Сценарий: {name}\n⚡ Скорость: {speed}\n🌍 Окружение: HOME"
    else:
        error = result.get("detail", "Неизвестная ошибка") if result else "Robot API недоступен"
        return f"❌ Ошибка запуска: {error}"


async def robot_stop() -> str:
    result = robot_service.stop()
    if result and result.get("status") == "stopping":
        return "🛑 Robot останавливается..."
    else:
        error = result.get("detail", "Робот не запущен") if result else "Robot API недоступен"
        return f"❌ {error}"


async def robot_stats() -> str:
    stats = robot_service.get_stats()
    if stats is None:
        return "🤖 Robot — API недоступен"

    lines = ["📊 Статистика Robot:"]
    if stats.get("total_operations") is not None:
        lines.append(f"Всего операций: {stats['total_operations']}")
    if stats.get("scenarios"):
        for s, data in stats["scenarios"].items():
            name = SCENARIO_NAMES.get(s, s)
            count = data.get("count", 0)
            lines.append(f"  {name}: {count}")
    return "\n".join(lines)


# =============================================================================
# HTTP /incoming handler (legacy, kept for compatibility)
# =============================================================================

async def handle_command(text: str) -> bool:
    """Route command via HTTP. Returns True if handled."""
    text = text.strip()
    cmd = text.split()[0].lower() if text else ""
    if cmd in ("/help", "/start", "/status", "/pods", "/metrics", "/robot"):
        # For HTTP path, send response via webhook
        result = await handle_command_text(cmd)
        if result:
            await uplink.send_message(text=result)
        return True
    return False
