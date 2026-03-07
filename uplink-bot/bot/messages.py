"""
Message formatters for Uplink bot.
HTML format for Matrix clients.
"""

from datetime import datetime


def format_money(value: float) -> str:
    formatted = f"{value:,.2f}".replace(",", " ")
    return f"{formatted} &#8381;"


# =============================================================================
# Health
# =============================================================================

def format_health_message(health_data: dict) -> tuple:
    """Returns (plaintext, html) tuple."""
    staging_api = health_data["staging_api"]
    staging_fe = health_data["staging_fe"]
    k8s = health_data["k8s"]

    def status_icon(s):
        return "&#9989;" if s.get("status") == "UP" else "&#10060;"

    def latency_str(s):
        return f" ({s.get('latency_ms', '?')}ms)" if s.get('latency_ms') else ""

    html = f"""<b>&#127973; Статус Homelab</b>
<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>

{status_icon(staging_api)} <b>API:</b> {staging_api.get('status')}{latency_str(staging_api)}
{status_icon(staging_fe)} <b>Frontend:</b> {staging_fe.get('status')}{latency_str(staging_fe)}
"""

    if k8s.get("pods"):
        html += "<br/><b>Сервисы:</b><br/>"
        for pod in k8s["pods"][:6]:
            icon = "&#128994;" if pod["status"] == "Running" else "&#128308;"
            restarts = f" (↻{pod['restarts']})" if pod['restarts'] != "0" else ""
            html += f"  {icon} {pod['name'][:25]}{restarts}<br/>"

    if k8s.get("node"):
        html += f"<br/><b>Ресурсы API:</b><br/>"
        html += f"  CPU: {k8s['node'].get('cpu_percent', '?')} | JVM RAM: {k8s['node'].get('memory_percent', '?')}<br/>"

    all_up = all(s.get("status") == "UP" for s in [staging_api, staging_fe])
    if all_up:
        html += "<br/><b>Все сервисы работают!</b>"
    else:
        html += "<br/><b>Есть проблемы!</b>"

    plain = f"Статус Homelab — API: {staging_api.get('status')}, Frontend: {staging_fe.get('status')}"
    return plain, html.strip()


# =============================================================================
# Robot
# =============================================================================

def format_robot_notification(scenario: str, result: dict) -> tuple:
    """Returns (plaintext, html) tuple for robot notification."""
    scenario_names = {
        "receiving": "Приёмка",
        "shipping": "Отгрузка",
        "inventory": "Инвентаризация",
    }

    has_error = result.get("error")
    emoji = "&#10060;" if has_error else "&#9989;"
    name = scenario_names.get(scenario, scenario)

    html = f"<b>{emoji} {name} завершена</b><br/><br/>"
    plain = f"{'❌' if has_error else '✅'} {name} завершена\n"

    if scenario == "receiving":
        products = result.get("products", [])
        if products:
            html += "<b>Добавленные товары:</b><br/>"
            for p in products:
                pname = p.get("name", "Товар")
                qty = p.get("quantity", 0)
                price = p.get("price", 0)
                total = qty * price
                html += f"  • {pname}: {qty} шт. × {format_money(price)} = {format_money(total)}<br/>"
            html += "<br/>"

        html += (
            f"<b>Итого:</b><br/>"
            f"• Создано товаров: {result.get('products_created', 0)}<br/>"
            f"• Всего единиц: {result.get('total_quantity', 0):,}<br/>"
            f"• На сумму: {format_money(result.get('total_value', 0))}"
        )
        plain += (
            f"Создано товаров: {result.get('products_created', 0)}, "
            f"единиц: {result.get('total_quantity', 0):,}, "
            f"сумма: {result.get('total_value', 0):.2f}"
        )

    elif scenario == "shipping":
        details = result.get("details", [])
        if details:
            html += "<b>Отгруженные товары:</b><br/>"
            for d in details:
                pname = d.get("product_name", "Товар")
                shipped = d.get("shipped_qty", 0)
                remaining = d.get("remaining_qty", 0)
                price = d.get("unit_price", 0)
                total = shipped * price
                html += f"  • {pname}: -{shipped} шт. (остаток: {remaining}) = {format_money(total)}<br/>"
            html += "<br/>"

        html += (
            f"<b>Итого:</b><br/>"
            f"• Позиций: {result.get('positions', 0)}<br/>"
            f"• Отгружено: {result.get('total_shipped', 0):,} ед.<br/>"
            f"• На сумму: {format_money(result.get('total_value', 0))}"
        )
        plain += (
            f"Позиций: {result.get('positions', 0)}, "
            f"отгружено: {result.get('total_shipped', 0):,}, "
            f"сумма: {result.get('total_value', 0):.2f}"
        )

    elif scenario == "inventory":
        adjustments = result.get("adjustments", [])
        deleted_products = result.get("deleted_products", [])

        if adjustments:
            html += "<b>Корректировки:</b><br/>"
            for a in adjustments:
                pname = a.get("product_name", "Товар")
                was = a.get("was", 0)
                now = a.get("now", 0)
                diff = a.get("diff", 0)
                sign = "+" if diff > 0 else ""
                adj_icon = "&#128200;" if diff > 0 else "&#128201;"
                html += f"  {adj_icon} {pname}: {was} → {now} ({sign}{diff})<br/>"
            html += "<br/>"

        if deleted_products:
            html += "<b>Списано:</b><br/>"
            for pname in deleted_products:
                html += f"  &#128465; {pname}<br/>"
            html += "<br/>"

        html += (
            f"<b>Итого:</b><br/>"
            f"• Корректировок: {result.get('adjusted', 0)}<br/>"
            f"• Излишки: {result.get('surplus_count', 0)}, недостачи: {result.get('shortage_count', 0)}<br/>"
            f"• Списано: {result.get('deleted', 0)}"
        )
        plain += (
            f"Корректировок: {result.get('adjusted', 0)}, "
            f"излишки: {result.get('surplus_count', 0)}, "
            f"недостачи: {result.get('shortage_count', 0)}, "
            f"списано: {result.get('deleted', 0)}"
        )

    return plain.strip(), html.strip()
