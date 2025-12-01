"""
Сценарий: Отгрузка товара со склада.
Эмулирует выполнение заказов клиентов.
"""
import random
import logging
from typing import Dict, Any, List

from .base import BaseScenario

logger = logging.getLogger(__name__)


class ShippingScenario(BaseScenario):
    """Сценарий: Отгрузка товара со склада."""

    name = "shipping"
    description = "Отгрузка товара — уменьшение остатков по заказам"

    def run(self) -> Dict[str, Any]:
        """
        Выполнить отгрузку: уменьшить quantity у 2-5 случайных товаров.

        Returns:
            Результат выполнения с деталями отгрузки
        """
        logger.info(f"🚚 Начинаем отгрузку по заказам")

        # Получаем товары с quantity > 0
        products = self.client.get_products()
        available = [p for p in products if p.get("quantity", 0) > 0]

        if not available:
            logger.warning("⚠️ Нет товаров для отгрузки — склад пуст!")
            return {
                "scenario": self.name,
                "description": self.description,
                "shipped": 0,
                "message": "Нет товаров для отгрузки",
                "stats": self.get_stats(),
            }

        # Выбираем 2-5 случайных товаров
        ship_count = min(random.randint(2, 5), len(available))
        to_ship = random.sample(available, ship_count)

        shipped: List[Dict[str, Any]] = []
        total_shipped_qty = 0
        total_value = 0

        for product in to_ship:
            current_qty = product.get("quantity", 0)
            # Отгружаем от 1 до 30% остатка (минимум 1, максимум 10)
            max_ship = max(1, min(10, current_qty // 3))
            ship_qty = random.randint(1, max_ship)
            new_qty = current_qty - ship_qty

            self.log_action(
                f"📤 Отгружаем: {product['name']} x{ship_qty} "
                f"(было: {current_qty}, осталось: {new_qty})"
            )

            # Формируем данные для обновления
            update_data = {
                "name": product["name"],
                "category": product.get("category", "Без категории"),
                "quantity": new_qty,
                "price": product.get("price", 0),
                "description": product.get("description", ""),
            }

            result = self.client.update_product(product["id"], update_data)

            if result:
                shipped.append({
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "category": product.get("category"),
                    "shipped_qty": ship_qty,
                    "remaining_qty": new_qty,
                    "unit_price": product.get("price", 0),
                })
                self.stats["products_updated"] += 1
                total_shipped_qty += ship_qty
                total_value += ship_qty * product.get("price", 0)
                logger.info(f"✅ Отгрузка выполнена: {product['name']}")
            else:
                self.stats["errors"] += 1
                logger.error(f"❌ Ошибка отгрузки: {product['name']}")

            # Пауза между действиями
            self.wait()

        # Итоговое сообщение
        logger.info(
            f"🏁 Отгрузка завершена: {len(shipped)} позиций, "
            f"{total_shipped_qty} единиц на сумму {total_value:.2f} ₽"
        )

        return {
            "scenario": self.name,
            "description": self.description,
            "positions": len(shipped),
            "total_shipped": total_shipped_qty,
            "total_value": round(total_value, 2),
            "details": shipped,
            "stats": self.get_stats(),
        }
