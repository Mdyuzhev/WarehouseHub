"""
Message formatters for the bot.
"""

from datetime import datetime


def format_money(value: float) -> str:
    formatted = f"{value:,.2f}".replace(",", " ")
    return f"{formatted} ₽"


# =============================================================================
# Health
# =============================================================================

def format_health_message(health_data: dict) -> str:
    staging_api = health_data["staging_api"]
    staging_fe = health_data["staging_fe"]
    prod_api = health_data["prod_api"]
    prod_fe = health_data["prod_fe"]
    k8s = health_data["k8s"]
    prod = health_data["prod"]

    def status_icon(s):
        return "✅" if s.get("status") == "UP" else "❌"

    def latency_str(s):
        return f" ({s.get('latency_ms', '?')}ms)" if s.get('latency_ms') else ""

    msg = f"""
<b>🏥 Статус серверов</b>
<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>

<b>━━━ 🧪 STAGING ━━━</b>
{status_icon(staging_api)} <b>API:</b> {staging_api.get('status')}{latency_str(staging_api)}
{status_icon(staging_fe)} <b>Frontend:</b> {staging_fe.get('status')}{latency_str(staging_fe)}
"""

    if k8s.get("pods"):
        msg += "\n<b>📦 Сервисы:</b>\n"
        for pod in k8s["pods"][:6]:
            icon = "🟢" if pod["status"] == "Running" else "🔴"
            restarts = f" (↻{pod['restarts']})" if pod['restarts'] != "0" else ""
            msg += f"  {icon} {pod['name'][:25]}{restarts}\n"

    if k8s.get("node"):
        msg += f"\n<b>💻 Ресурсы:</b>\n"
        msg += f"  CPU: {k8s['node'].get('cpu_percent', '?')} | RAM: {k8s['node'].get('memory_percent', '?')}\n"

    msg += f"""
<b>━━━ 🚀 PRODUCTION ━━━</b>
{status_icon(prod_api)} <b>API:</b> {prod_api.get('status')}{latency_str(prod_api)}
{status_icon(prod_fe)} <b>Frontend:</b> {prod_fe.get('status')}{latency_str(prod_fe)}
"""

    if prod.get("containers"):
        msg += "\n<b>🐳 Контейнеры:</b>\n"
        for c in prod["containers"][:6]:
            icon = "🟢" if c["status"] == "UP" else "🔴"
            msg += f"  {icon} {c['name']}\n"

    all_up = all(s.get("status") == "UP" for s in [staging_api, staging_fe, prod_api, prod_fe])
    if all_up:
        msg += "\n✨ <b>Все сервисы работают!</b>"
    else:
        msg += "\n⚠️ <b>Есть проблемы с сервисами!</b>"

    return msg.strip()


# =============================================================================
# Robot
# =============================================================================

ROBOT_JOKES = {
    "started": [
        "Робот поехал!",
        "Сценарий запущен!",
        "Поехали!",
    ],
    "stopped": [
        "Робот остановлен.",
        "Стоп машина!",
    ],
    "error": [
        "Что-то пошло не так!",
        "Робот споткнулся...",
    ],
}


def format_robot_menu(status: dict) -> str:
    state = status.get("state", "unknown")
    current_scenario = status.get("current_scenario")

    state_emoji = {"idle": "😴", "running": "🏃", "stopping": "🛑", "error": "❌"}
    state_text = {"idle": "Ожидание", "running": "Работает", "stopping": "Останавливается", "error": "Ошибка"}

    msg = f"""🤖 *Warehouse Robot*

{state_emoji.get(state, '❓')} *Статус:* {state_text.get(state, state)}
"""

    if current_scenario:
        scenario_names = {
            "receiving": "📦 Приёмка",
            "shipping": "🚚 Отгрузка",
            "inventory": "📋 Инвентаризация",
        }
        msg += f"🎬 *Сценарий:* {scenario_names.get(current_scenario, current_scenario)}\n"

    return msg.strip()


def format_robot_status(status: dict, health: dict) -> str:
    state = status.get("state", "unknown")
    api_available = health.get("api_available", False)

    return f"""🤖 *Статус Warehouse Robot*

*Робот:*
• Состояние: {state}
• Текущий сценарий: {status.get('current_scenario', '-')}
• Uptime: {status.get('uptime_seconds', 0):.0f}с

*Warehouse API:*
• Доступен: {'✅ Да' if api_available else '❌ Нет'}"""


def format_robot_stats(stats: dict) -> str:
    total = stats.get("total_runs", 0)
    success = stats.get("successful_runs", 0)
    failed = stats.get("failed_runs", 0)
    last_scenario = stats.get("last_scenario", "-")

    last_result = stats.get("last_result", {})
    result_details = ""

    if last_result:
        scenario = last_result.get("scenario", "")
        if scenario == "receiving":
            result_details = f"""
📦 *Последняя приёмка:*
• Создано товаров: {last_result.get('products_created', 0)}
• Всего единиц: {last_result.get('total_quantity', 0):,}
• На сумму: {format_money(last_result.get('total_value', 0))}
"""
        elif scenario == "shipping":
            result_details = f"""
🚚 *Последняя отгрузка:*
• Позиций: {last_result.get('positions', 0)}
• Отгружено: {last_result.get('total_shipped', 0):,} ед.
• На сумму: {format_money(last_result.get('total_value', 0))}
"""
        elif scenario == "inventory":
            result_details = f"""
📋 *Последняя инвентаризация:*
• Корректировок: {last_result.get('adjusted', 0)}
• Излишки: {last_result.get('surplus_count', 0)}
• Недостачи: {last_result.get('shortage_count', 0)}
• Списано: {last_result.get('deleted', 0)}
"""

    return f"""📊 *Статистика Warehouse Robot*

*Общая статистика:*
• Всего запусков: {total}
• Успешных: ✅ {success}
• С ошибками: ❌ {failed}

*Последний запуск:*
• Сценарий: {last_scenario}
{result_details}""".strip()


def format_robot_started(scenario: str, speed: str, environment: str = "staging", duration: int = 0) -> str:
    scenario_names = {
        "receiving": "📦 Приёмка товара",
        "shipping": "🚚 Отгрузка",
        "inventory": "📋 Инвентаризация",
        "all": "🎲 Все сценарии",
    }
    speed_names = {
        "slow": "🐢 Медленно (15с)",
        "normal": "🚶 Нормально (5с)",
        "fast": "🚀 Быстро (1с)",
    }
    env_names = {
        "staging": "🔧 STAGING",
        "prod": "🚀 PROD",
    }
    duration_names = {0: "один раз", 5: "5 минут", 30: "30 минут", 60: "1 час"}

    return f"""✅ *Сценарий запущен!*

🎬 *Сценарий:* {scenario_names.get(scenario, scenario)}
⏱ *Продолжительность:* {duration_names.get(duration, f"{duration} мин")}
🌍 *Окружение:* {env_names.get(environment, environment)}
⚡ *Скорость:* {speed_names.get(speed, speed)}
"""


def format_robot_stopped() -> str:
    return "🛑 *Робот останавливается...*"


def format_robot_error(error: str) -> str:
    return f"❌ *Ошибка:* {error}"


def format_robot_notification(scenario: str, result: dict) -> str:
    scenario_names = {
        "receiving": "📦 Приёмка",
        "shipping": "🚚 Отгрузка",
        "inventory": "📋 Инвентаризация",
    }

    emoji = "✅" if not result.get("error") else "❌"
    msg = f"""{emoji} *{scenario_names.get(scenario, scenario)} завершена*

"""

    if scenario == "receiving":
        products = result.get("products", [])
        if products:
            msg += "*Добавленные товары:*\n"
            for p in products:
                name = p.get("name", "Товар")
                qty = p.get("quantity", 0)
                price = p.get("price", 0)
                total = qty * price
                msg += f"  • {name}: {qty} шт. × {format_money(price).replace(' ₽', '')} = {format_money(total)}\n"
            msg += "\n"

        msg += f"""*Итого:*
• Создано товаров: {result.get('products_created', 0)}
• Всего единиц: {result.get('total_quantity', 0):,}
• На сумму: {format_money(result.get('total_value', 0))}"""

    elif scenario == "shipping":
        details = result.get("details", [])
        if details:
            msg += "*Отгруженные товары:*\n"
            for d in details:
                name = d.get("product_name", "Товар")
                shipped = d.get("shipped_qty", 0)
                remaining = d.get("remaining_qty", 0)
                price = d.get("unit_price", 0)
                total = shipped * price
                msg += f"  • {name}: -{shipped} шт. (остаток: {remaining}) = {format_money(total)}\n"
            msg += "\n"

        msg += f"""*Итого:*
• Позиций: {result.get('positions', 0)}
• Отгружено: {result.get('total_shipped', 0):,} ед.
• На сумму: {format_money(result.get('total_value', 0))}"""

    elif scenario == "inventory":
        adjustments = result.get("adjustments", [])
        deleted_products = result.get("deleted_products", [])

        if adjustments:
            msg += "*Корректировки:*\n"
            for a in adjustments:
                name = a.get("product_name", "Товар")
                was = a.get("was", 0)
                now = a.get("now", 0)
                diff = a.get("diff", 0)
                sign = "+" if diff > 0 else ""
                emoji_adj = "📈" if diff > 0 else "📉"
                msg += f"  {emoji_adj} {name}: {was} → {now} ({sign}{diff})\n"
            msg += "\n"

        if deleted_products:
            msg += "*Списано:*\n"
            for name in deleted_products:
                msg += f"  🗑️ {name}\n"
            msg += "\n"

        msg += f"""*Итого:*
• Корректировок: {result.get('adjusted', 0)}
• Излишки: {result.get('surplus_count', 0)}, недостачи: {result.get('shortage_count', 0)}
• Списано: {result.get('deleted', 0)}"""

    return msg.strip()
