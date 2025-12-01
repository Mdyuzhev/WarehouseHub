#!/usr/bin/env python3
"""
Warehouse Robot CLI — командная строка для управления роботом-симулятором.

Использование:
    python robot.py run <scenario> [--speed slow|normal|fast]
    python robot.py list
    python robot.py status
    python robot.py api [--host 0.0.0.0] [--port 8070]

Примеры:
    python robot.py run receiving --speed fast
    python robot.py run shipping
    python robot.py run inventory --speed slow
    python robot.py list
    python robot.py api
"""
import argparse
import logging
import sys

from api_client import WarehouseAPIClient
from config import settings
from scenarios import SCENARIOS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_run(args):
    """Запуск сценария напрямую через CLI."""
    scenario_name = args.scenario
    speed = args.speed

    if scenario_name not in SCENARIOS:
        print(f"❌ Неизвестный сценарий: {scenario_name}")
        print(f"   Доступные сценарии: {', '.join(SCENARIOS.keys())}")
        return 1

    print(f"🤖 Запуск сценария: {scenario_name} (speed={speed})")
    print(f"📡 API URL: {settings.api_url}")
    print()

    try:
        with WarehouseAPIClient() as client:
            # Авторизация
            print("🔐 Авторизация...")
            if not client.login():
                print("❌ Ошибка авторизации!")
                return 1
            print("✅ Авторизация успешна")
            print()

            # Создание и запуск сценария
            scenario_class = SCENARIOS[scenario_name]
            scenario = scenario_class(client, speed=speed)

            print(f"▶️  Выполнение: {scenario.description}")
            print("-" * 50)

            result = scenario.run()

            print("-" * 50)
            print()
            print("📊 Результат:")
            print_result(scenario_name, result)

            return 0

    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
        return 130

    except Exception as e:
        logger.exception(f"Ошибка выполнения: {e}")
        print(f"❌ Ошибка: {e}")
        return 1


def print_result(scenario_name: str, result: dict):
    """Красивый вывод результата сценария."""
    if scenario_name == "receiving":
        print(f"   📦 Создано товаров: {result.get('products_created', 0)}")
        print(f"   📊 Всего единиц: {result.get('total_quantity', 0)}")
        print(f"   💰 На сумму: {result.get('total_value', 0):.2f} ₽")

    elif scenario_name == "shipping":
        print(f"   🚚 Позиций отгружено: {result.get('positions', 0)}")
        print(f"   📊 Всего единиц: {result.get('total_shipped', 0)}")
        print(f"   💰 На сумму: {result.get('total_value', 0):.2f} ₽")

    elif scenario_name == "inventory":
        print(f"   📋 Корректировок: {result.get('adjusted', 0)}")
        print(f"      ↗️ Излишки: {result.get('surplus_count', 0)}")
        print(f"      ↘️ Недостачи: {result.get('shortage_count', 0)}")
        print(f"   🗑️ Списано товаров: {result.get('deleted', 0)}")

    # Общая статистика
    stats = result.get("stats", {})
    if stats:
        print()
        print("   📈 Статистика операций:")
        print(f"      Действий: {stats.get('actions', 0)}")
        if stats.get("products_created"):
            print(f"      Создано: {stats.get('products_created', 0)}")
        if stats.get("products_updated"):
            print(f"      Обновлено: {stats.get('products_updated', 0)}")
        if stats.get("products_deleted"):
            print(f"      Удалено: {stats.get('products_deleted', 0)}")
        if stats.get("errors"):
            print(f"      ❌ Ошибок: {stats.get('errors', 0)}")


def cmd_list(args):
    """Список доступных сценариев."""
    print("📋 Доступные сценарии:")
    print()
    for name, scenario_class in SCENARIOS.items():
        print(f"   • {name}")
        print(f"     {scenario_class.description}")
        print()
    return 0


def cmd_status(args):
    """Статус API склада."""
    print("🔍 Проверка статуса Warehouse API...")
    print(f"   URL: {settings.api_url}")
    print()

    try:
        with WarehouseAPIClient() as client:
            if client.health_check():
                print("✅ API доступен")

                # Пробуем авторизоваться
                print("🔐 Проверка авторизации...")
                if client.login():
                    print("✅ Авторизация успешна")

                    # Получаем количество товаров
                    products = client.get_products()
                    print(f"📦 Товаров на складе: {len(products)}")
                else:
                    print("⚠️ Ошибка авторизации")
            else:
                print("❌ API недоступен")
                return 1

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return 1

    return 0


def cmd_api(args):
    """Запуск API сервера."""
    import uvicorn
    from api import app

    host = args.host or "0.0.0.0"
    port = args.port or settings.api_port

    print(f"🤖 Запуск Warehouse Robot API")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Warehouse API: {settings.api_url}")
    print()

    uvicorn.run(app, host=host, port=port)
    return 0


def main():
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(
        description="🤖 Warehouse Robot CLI — управление роботом-симулятором склада",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python robot.py run receiving --speed fast
  python robot.py run shipping
  python robot.py list
  python robot.py status
  python robot.py api --port 8070
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Команда")

    # run
    run_parser = subparsers.add_parser(
        "run",
        help="Запустить сценарий",
    )
    run_parser.add_argument(
        "scenario",
        choices=list(SCENARIOS.keys()),
        help="Название сценария",
    )
    run_parser.add_argument(
        "--speed", "-s",
        choices=["slow", "normal", "fast"],
        default="normal",
        help="Скорость выполнения (default: normal)",
    )
    run_parser.set_defaults(func=cmd_run)

    # list
    list_parser = subparsers.add_parser(
        "list",
        help="Список сценариев",
    )
    list_parser.set_defaults(func=cmd_list)

    # status
    status_parser = subparsers.add_parser(
        "status",
        help="Статус Warehouse API",
    )
    status_parser.set_defaults(func=cmd_status)

    # api
    api_parser = subparsers.add_parser(
        "api",
        help="Запустить API сервер",
    )
    api_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host для API (default: 0.0.0.0)",
    )
    api_parser.add_argument(
        "--port", "-p",
        type=int,
        default=settings.api_port,
        help=f"Port для API (default: {settings.api_port})",
    )
    api_parser.set_defaults(func=cmd_api)

    # Parse
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
