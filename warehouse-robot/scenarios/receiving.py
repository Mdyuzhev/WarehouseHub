"""
Сценарий: Приёмка товара на склад.
Эмулирует поступление новых товаров от поставщиков.
"""
import random
import logging
from typing import Dict, Any, List
from faker import Faker

from .base import BaseScenario

logger = logging.getLogger(__name__)
fake = Faker("ru_RU")

# Шаблоны товаров по категориям
PRODUCT_TEMPLATES = {
    "Электроника": [
        "Ноутбук {brand}",
        "Смартфон {brand}",
        "Планшет {brand}",
        "Наушники {brand}",
        "Клавиатура {brand}",
        "Мышь {brand}",
        "Монитор {brand}",
        "Веб-камера {brand}",
        "USB-хаб {brand}",
        "SSD накопитель {brand}",
        "Видеокарта {brand}",
        "Роутер {brand}",
    ],
    "Одежда": [
        "Футболка {color}",
        "Джинсы {color}",
        "Куртка {color}",
        "Кроссовки {brand}",
        "Рубашка {color}",
        "Свитер {color}",
        "Пальто {color}",
        "Шапка {color}",
        "Перчатки {color}",
    ],
    "Продукты": [
        "Кофе {brand}",
        "Чай {brand}",
        "Печенье {brand}",
        "Шоколад {brand}",
        "Вода {brand}",
        "Сок {brand}",
        "Орехи {brand}",
        "Хлопья {brand}",
    ],
    "Инструменты": [
        "Дрель {brand}",
        "Шуруповёрт {brand}",
        "Молоток",
        "Отвёртка набор",
        "Пассатижи",
        "Рулетка {brand}",
        "Уровень строительный",
        "Ключ разводной",
        "Пила ручная",
    ],
    "Бытовая техника": [
        "Чайник {brand}",
        "Микроволновка {brand}",
        "Блендер {brand}",
        "Пылесос {brand}",
        "Утюг {brand}",
        "Кофеварка {brand}",
        "Тостер {brand}",
        "Миксер {brand}",
        "Мультиварка {brand}",
    ],
    "Канцелярия": [
        "Ручка гелевая",
        "Карандаш {brand}",
        "Тетрадь 96 листов",
        "Папка-скоросшиватель",
        "Степлер {brand}",
        "Ножницы офисные",
        "Скотч упаковочный",
        "Маркер {color}",
    ],
}

# Бренды для генерации
BRANDS = [
    "Samsung", "LG", "Sony", "Bosch", "Philips", "Xiaomi",
    "Apple", "ASUS", "Dell", "HP", "Lenovo", "Huawei",
    "Canon", "Nikon", "JBL", "Logitech", "Microsoft",
]

# Цвета для генерации
COLORS = [
    "синий", "чёрный", "белый", "серый", "красный",
    "зелёный", "бежевый", "коричневый", "розовый", "голубой",
]


class ReceivingScenario(BaseScenario):
    """Сценарий: Приёмка товара на склад."""

    name = "receiving"
    description = "Приёмка товара — создание новых позиций на складе"

    def generate_product(self) -> Dict[str, Any]:
        """
        Генерация случайного товара с реалистичными данными.

        Returns:
            Словарь с данными товара
        """
        # Выбираем случайную категорию и шаблон
        category = random.choice(list(PRODUCT_TEMPLATES.keys()))
        template = random.choice(PRODUCT_TEMPLATES[category])

        # Формируем название
        name = template.format(
            brand=random.choice(BRANDS),
            color=random.choice(COLORS),
        )

        # Генерируем цену в зависимости от категории
        price_ranges = {
            "Электроника": (5000, 150000),
            "Одежда": (500, 15000),
            "Продукты": (50, 1000),
            "Инструменты": (200, 10000),
            "Бытовая техника": (1000, 50000),
            "Канцелярия": (10, 500),
        }
        min_price, max_price = price_ranges.get(category, (100, 5000))

        return {
            "name": name,
            "category": category,
            "quantity": random.randint(1, 3),  # Мало единиц чтобы не забивать базу
            "price": round(random.uniform(min_price, max_price), 2),
            "description": f"Поставка от {fake.company()}. Партия #{random.randint(1000, 9999)}",
        }

    def run(self) -> Dict[str, Any]:
        """
        Выполнить приёмку: создать 1-3 случайных товаров.

        Returns:
            Результат выполнения с созданными товарами
        """
        logger.info(f"🚚 Начинаем приёмку товара")

        # Определяем количество товаров для приёмки (1-3 чтобы не забивать базу)
        products_count = random.randint(1, 3)
        created: List[Dict[str, Any]] = []

        for i in range(products_count):
            product_data = self.generate_product()
            self.log_action(f"📦 Принимаем: {product_data['name']} x{product_data['quantity']}")

            result = self.client.create_product(product_data)

            if result:
                created.append(result)
                self.stats["products_created"] += 1
                logger.info(f"✅ Товар создан: ID={result.get('id')}")
            else:
                self.stats["errors"] += 1
                logger.error(f"❌ Ошибка создания товара: {product_data['name']}")

            # Пауза между действиями
            if i < products_count - 1:
                self.wait()

        # Итоговое сообщение
        total_qty = sum(p.get("quantity", 0) for p in created)
        total_value = sum(p.get("quantity", 0) * p.get("price", 0) for p in created)

        logger.info(
            f"🏁 Приёмка завершена: {len(created)} товаров, "
            f"{total_qty} единиц на сумму {total_value:.2f} ₽"
        )

        return {
            "scenario": self.name,
            "description": self.description,
            "products_created": len(created),
            "total_quantity": total_qty,
            "total_value": round(total_value, 2),
            "products": created,
            "stats": self.get_stats(),
        }
