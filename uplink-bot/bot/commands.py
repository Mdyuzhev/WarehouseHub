"""
Command handlers for Uplink bot.
Processes /wh commands from Matrix users via WS bridge.
Supports inline buttons (uplink.buttons).
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


def reply(text: str, buttons: list = None) -> dict:
    """Build structured response with optional buttons."""
    resp = {"text": text}
    if buttons:
        resp["buttons"] = buttons
    return resp


# =============================================================================
# WS bridge handler (returns structured response for Matrix)
# =============================================================================

async def handle_command_text(cmd: str, args: list = None) -> dict:
    """Process command and return structured response {text, buttons?}."""
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
    return reply(f"Unknown command: {cmd}. Use /wh help.")


async def handle_callback(callback_data: str) -> dict:
    """Handle button callback. Returns structured response."""
    logger.info(f"Callback: {callback_data}")

    handlers = {
        "cmd_status": lambda: get_status_text(),
        "cmd_pods": lambda: get_pods_text(),
        "cmd_metrics": lambda: get_metrics_text(),
        "cmd_robot": lambda: get_robot_text([]),
        "cmd_help": lambda: get_help_text(),
        "robot_status": lambda: get_robot_text([]),
        "robot_stop": lambda: get_robot_text(["stop"]),
        "robot_stats": lambda: get_robot_text(["stats"]),
        "robot_start_receiving": lambda: get_robot_text(["start", "receiving"]),
        "robot_start_shipping": lambda: get_robot_text(["start", "shipping"]),
        "robot_start_inventory": lambda: get_robot_text(["start", "inventory"]),
    }

    handler = handlers.get(callback_data)
    if handler:
        return await handler()
    return reply(f"Unknown callback: {callback_data}")


async def get_help_text() -> dict:
    text = (
        "🤖 WarehouseHub Bot\n\n"
        "/wh status — статус серверов\n"
        "/wh pods — сервисы\n"
        "/wh metrics — CPU / RAM\n"
        "/wh robot — статус робота\n"
        "/wh robot start <scenario> — запуск\n"
        "/wh robot stop — остановка\n"
        "/wh robot stats — статистика\n"
        "/wh help — справка"
    )
    buttons = [
        [
            {"label": "📊 Статус", "callback": "cmd_status"},
            {"label": "📦 Сервисы", "callback": "cmd_pods"},
        ],
        [
            {"label": "💻 Метрики", "callback": "cmd_metrics"},
            {"label": "🤖 Робот", "callback": "cmd_robot"},
        ],
    ]
    return reply(text, buttons)


async def get_status_text() -> dict:
    health_data = await check_all_health()
    lines = ["🏥 Статус:"]
    for key in ("staging_api", "staging_fe"):
        svc = health_data.get(key, {})
        icon = "🟢" if svc.get("status") == "UP" else "🔴"
        name = svc.get("name", key)
        latency = f" ({svc.get('latency_ms', '?')}ms)" if svc.get("latency_ms") else ""
        lines.append(f"{icon} {name}{latency}")
    buttons = [
        [
            {"label": "🔄 Обновить", "callback": "cmd_status"},
            {"label": "📦 Сервисы", "callback": "cmd_pods"},
        ],
        [
            {"label": "💻 Метрики", "callback": "cmd_metrics"},
            {"label": "🤖 Робот", "callback": "cmd_robot"},
        ],
    ]
    return reply("\n".join(lines), buttons)


async def get_pods_text() -> dict:
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
    text = "\n".join(lines) if len(lines) > 1 else "No service data"
    buttons = [
        [
            {"label": "🔄 Обновить", "callback": "cmd_pods"},
            {"label": "📊 Статус", "callback": "cmd_status"},
        ],
    ]
    return reply(text, buttons)


async def get_metrics_text() -> dict:
    k8s = await get_k8s_resources()
    node = k8s.get("node", {})
    if node:
        text = f"📊 Метрики:\nCPU: {node.get('cpu_percent', 'N/A')}\nRAM: {node.get('memory_percent', 'N/A')}"
    else:
        text = "Метрики недоступны"
    buttons = [
        [
            {"label": "🔄 Обновить", "callback": "cmd_metrics"},
            {"label": "📊 Статус", "callback": "cmd_status"},
        ],
    ]
    return reply(text, buttons)


async def get_robot_text(args: list = None) -> dict:
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


async def robot_status() -> dict:
    status = robot_service.get_status()
    if status is None:
        return reply("🤖 Robot — API недоступен", [
            [{"label": "🔄 Обновить", "callback": "robot_status"}],
        ])

    is_running = status.get("running", False)
    scenario = status.get("scenario", "—")
    icon = "🟢" if is_running else "⚪"
    text = f"🤖 Robot: {icon} {'запущен' if is_running else 'остановлен'}"
    if is_running:
        text += f"\n📋 Сценарий: {SCENARIO_NAMES.get(scenario, scenario)}"
        if status.get("operations_done") is not None:
            text += f"\n📊 Операций: {status['operations_done']}"

    if is_running:
        buttons = [
            [
                {"label": "⏹ Стоп", "callback": "robot_stop"},
                {"label": "📊 Статистика", "callback": "robot_stats"},
            ],
            [{"label": "🔄 Обновить", "callback": "robot_status"}],
        ]
    else:
        buttons = [
            [
                {"label": "▶ Приёмка", "callback": "robot_start_receiving"},
                {"label": "▶ Отгрузка", "callback": "robot_start_shipping"},
            ],
            [
                {"label": "▶ Инвентаризация", "callback": "robot_start_inventory"},
                {"label": "📊 Статистика", "callback": "robot_stats"},
            ],
        ]
    return reply(text, buttons)


async def robot_start(args: list) -> dict:
    if not args:
        buttons = [
            [
                {"label": "▶ Приёмка", "callback": "robot_start_receiving"},
                {"label": "▶ Отгрузка", "callback": "robot_start_shipping"},
            ],
            [{"label": "▶ Инвентаризация", "callback": "robot_start_inventory"}],
        ]
        return reply("Выберите сценарий:", buttons)

    scenario = args[0].lower()
    if scenario not in SCENARIOS:
        return reply(f"❌ Неизвестный сценарий: {scenario}\nДоступные: {', '.join(SCENARIOS)}")

    # Check if already running
    status = robot_service.get_status()
    if status and status.get("running"):
        return reply(
            f"⚠️ Robot уже запущен ({status.get('scenario')}). Сначала остановите.",
            [[{"label": "⏹ Стоп", "callback": "robot_stop"}]],
        )

    speed = args[1] if len(args) > 1 and args[1] in ("slow", "normal", "fast") else "normal"
    result = robot_service.start_scenario(scenario, speed=speed, environment="home")

    if result and result.get("status") == "started":
        name = SCENARIO_NAMES.get(scenario, scenario)
        return reply(
            f"🚀 Robot запущен!\n📋 Сценарий: {name}\n⚡ Скорость: {speed}\n🌍 Окружение: HOME",
            [
                [
                    {"label": "⏹ Стоп", "callback": "robot_stop"},
                    {"label": "📊 Статистика", "callback": "robot_stats"},
                ],
                [{"label": "🔄 Статус", "callback": "robot_status"}],
            ],
        )
    else:
        error = result.get("detail", "Неизвестная ошибка") if result else "Robot API недоступен"
        return reply(f"❌ Ошибка запуска: {error}")


async def robot_stop() -> dict:
    result = robot_service.stop()
    if result and result.get("status") == "stopping":
        return reply("🛑 Robot останавливается...", [
            [{"label": "🔄 Статус", "callback": "robot_status"}],
        ])
    else:
        error = result.get("detail", "Робот не запущен") if result else "Robot API недоступен"
        return reply(f"❌ {error}")


async def robot_stats() -> dict:
    stats = robot_service.get_stats()
    if stats is None:
        return reply("🤖 Robot — API недоступен", [
            [{"label": "🔄 Обновить", "callback": "robot_stats"}],
        ])

    lines = ["📊 Статистика Robot:"]
    if stats.get("total_operations") is not None:
        lines.append(f"Всего операций: {stats['total_operations']}")
    if stats.get("scenarios"):
        for s, data in stats["scenarios"].items():
            name = SCENARIO_NAMES.get(s, s)
            count = data.get("count", 0)
            lines.append(f"  {name}: {count}")
    return reply("\n".join(lines), [
        [
            {"label": "🤖 Статус", "callback": "robot_status"},
            {"label": "🔄 Обновить", "callback": "robot_stats"},
        ],
    ])


# =============================================================================
# HTTP /incoming handler (legacy, kept for compatibility)
# =============================================================================

async def handle_command(text: str) -> bool:
    """Route command via HTTP. Returns True if handled."""
    text = text.strip()
    cmd = text.split()[0].lower() if text else ""
    if cmd in ("/help", "/start", "/status", "/pods", "/metrics", "/robot"):
        # For HTTP path, send response via webhook (no buttons support)
        result = await handle_command_text(cmd)
        if result:
            msg = result.get("text", "") if isinstance(result, dict) else result
            await uplink.send_message(text=msg)
        return True
    return False
