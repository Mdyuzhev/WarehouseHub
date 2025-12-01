"""
Сценарий: Инвентаризация склада.
Эмулирует проверку остатков, корректировку и списание.
"""
import random
import logging
from typing import Dict, Any, List

from .base import BaseScenario

logger = logging.getLogger(__name__)


class InventoryScenario(BaseScenario):
    """Сценарий: Инвентаризация склада."""

    name = "inventory"
    description = "Инвентаризация — корректировка остатков и очистка"

    def run(self) -> Dict[str, Any]:
        """
        Выполнить инвентаризацию:
        1. Корректировка остатков у случайных товаров (±)
        2. Удаление товаров с нулевым количеством

        Returns:
            Результат выполнения с деталями корректировок
        """
        logger.info(f"📋 Начинаем инвентаризацию склада")

        # Получаем все товары
        products = self.client.get_products()

        if not products:
            logger.warning("⚠️ Склад пуст — нечего инвентаризировать")
            return {
                "scenario": self.name,
                "description": self.description,
                "adjusted": 0,
                "deleted": 0,
                "message": "Склад пуст",
                "stats": self.get_stats(),
            }

        adjusted: List[Dict[str, Any]] = []
        deleted: List[str] = []

        # 1. КОРРЕКТИРОВКА ОСТАТКОВ
        # Выбираем 2-5 случайных товаров для корректировки
        adjust_count = min(random.randint(2, 5), len(products))
        to_adjust = random.sample(products, adjust_count)

        for product in to_adjust:
            current_qty = product.get("quantity", 0)

            # Случайная корректировка: от -5 до +10
            # Недостача бывает реже, чем обнаружение лишнего
            if random.random() < 0.3:  # 30% вероятность недостачи
                adjustment = random.randint(-5, -1)
            else:  # 70% вероятность обнаружения лишнего или точного совпадения
                adjustment = random.randint(0, 10)

            new_qty = max(0, current_qty + adjustment)

            # Пропускаем если количество не изменилось
            if new_qty == current_qty:
                logger.debug(f"⏩ {product['name']}: количество верное ({current_qty})")
                continue

            # Логируем действие
            if adjustment > 0:
                self.log_action(f"📈 Нашли лишнее: {product['name']} +{adjustment} (было {current_qty}, стало {new_qty})")
            else:
                self.log_action(f"📉 Недостача: {product['name']} {adjustment} (было {current_qty}, стало {new_qty})")

            # Обновляем товар
            update_data = {
                "name": product["name"],
                "category": product.get("category", "Без категории"),
                "quantity": new_qty,
                "price": product.get("price", 0),
                "description": product.get("description", ""),
            }

            result = self.client.update_product(product["id"], update_data)

            if result:
                adjusted.append({
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "was": current_qty,
                    "now": new_qty,
                    "diff": adjustment,
                })
                self.stats["products_updated"] += 1
            else:
                self.stats["errors"] += 1
                logger.error(f"❌ Ошибка корректировки: {product['name']}")

            self.wait()

        # 2. УДАЛЕНИЕ ТОВАРОВ С НУЛЕВЫМ ОСТАТКОМ
        # Обновляем список после корректировок
        products = self.client.get_products()
        zero_qty = [p for p in products if p.get("quantity", 0) == 0]

        # Удаляем максимум 3 товара за раз
        for product in zero_qty[:3]:
            self.log_action(f"🗑️ Списание: {product['name']} (нулевой остаток)")

            if self.client.delete_product(product["id"]):
                deleted.append(product["name"])
                self.stats["products_deleted"] += 1
                logger.info(f"✅ Товар списан: {product['name']}")
            else:
                self.stats["errors"] += 1
                logger.error(f"❌ Ошибка списания: {product['name']}")

            self.wait()

        # Подсчёт итогов
        surplus = sum(1 for a in adjusted if a["diff"] > 0)
        shortage = sum(1 for a in adjusted if a["diff"] < 0)

        logger.info(
            f"🏁 Инвентаризация завершена: "
            f"{len(adjusted)} корректировок (излишки: {surplus}, недостачи: {shortage}), "
            f"{len(deleted)} списаний"
        )

        return {
            "scenario": self.name,
            "description": self.description,
            "adjusted": len(adjusted),
            "surplus_count": surplus,
            "shortage_count": shortage,
            "deleted": len(deleted),
            "adjustments": adjusted,
            "deleted_products": deleted,
            "stats": self.get_stats(),
        }
