"""
Сценарий нагрузочного тестирования для warehouse-api.
WH-103: A/B тестирование Redis + Kafka

Оптимизировано: добавлен кэш токенов для снижения нагрузки BCrypt
"""

import random
import string
import time
import threading
from locust import HttpUser, task, between
from locust import LoadTestShape


# ============== ГЛОБАЛЬНЫЙ КЭШ ТОКЕНОВ ==============
# Токен получаем 1 раз на роль, переиспользуем для всех users этой роли
TOKEN_CACHE = {}
TOKEN_CACHE_LOCK = threading.Lock()


CATEGORIES = ["Электроника", "Одежда", "Продукты", "Инструменты", "Бытовая техника"]


class WarehouseUser(HttpUser):
    """Базовый класс пользователя склада."""

    wait_time = between(1, 3)
    username = None
    password = None
    role = None
    abstract = True

    def on_start(self):
        self.token = None
        self.created_product_ids = []
        self.login_with_cache()

    def on_stop(self):
        # Cleanup созданных продуктов
        for product_id in self.created_product_ids:
            try:
                self.client.delete(
                    f"/api/products/{product_id}",
                    headers=self.auth_headers(),
                    name="/api/products/[id] (cleanup)"
                )
            except:
                pass

    def login_with_cache(self):
        """Логин с кэшированием токена по роли."""
        cache_key = self.username

        # Проверяем кэш (thread-safe)
        with TOKEN_CACHE_LOCK:
            if cache_key in TOKEN_CACHE:
                self.token = TOKEN_CACHE[cache_key]
                return True

        # Токена нет в кэше — делаем реальный логин
        return self.login_with_retry()

    def login_with_retry(self, max_retries=3):
        """Логин с retry и сохранением в кэш."""
        cache_key = self.username

        for attempt in range(max_retries):
            try:
                response = self.client.post(
                    "/api/auth/login",
                    json={"username": self.username, "password": self.password},
                    name="/api/auth/login"
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("token")
                    if self.token:
                        # Сохраняем в глобальный кэш
                        with TOKEN_CACHE_LOCK:
                            TOKEN_CACHE[cache_key] = self.token
                        return True
            except Exception as e:
                pass
            time.sleep(0.5 * (attempt + 1))
        return False

    def ensure_logged_in(self):
        """Проверка что токен есть, при необходимости — повторный логин."""
        if not self.token:
            return self.login_with_cache()
        return True

    def auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def generate_product_name(self):
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"LoadTest-{self.role}-{suffix}"

    def generate_product_data(self):
        """Генерация полных данных продукта с description и category."""
        return {
            "name": self.generate_product_name(),
            "quantity": random.randint(1, 100),
            "price": round(random.uniform(10.0, 1000.0), 2),
            "description": f"Тестовый товар от {self.role}",
            "category": random.choice(CATEGORIES)
        }

    @task(5)
    def view_products(self):
        """GET /api/products - список всех товаров."""
        if not self.ensure_logged_in():
            return
        self.client.get("/api/products", headers=self.auth_headers(), name="/api/products (GET)")

    @task(2)
    def view_products_by_category(self):
        """GET /api/products?category=... - фильтрация по категории."""
        if not self.ensure_logged_in():
            return
        category = random.choice(CATEGORIES)
        self.client.get(
            f"/api/products?category={category}",
            headers=self.auth_headers(),
            name="/api/products?category (GET)"
        )

    @task(1)
    def view_current_user(self):
        """GET /api/auth/me - текущий пользователь."""
        if not self.ensure_logged_in():
            return
        self.client.get("/api/auth/me", headers=self.auth_headers(), name="/api/auth/me")


class SuperUser(WarehouseUser):
    """SUPER_USER - полный доступ ко всему."""
    weight = 1
    username = "superuser"
    password = "password123"
    role = "superuser"
    abstract = False

    @task(3)
    def create_product(self):
        """POST /api/products - создание товара."""
        if not self.ensure_logged_in():
            return
        response = self.client.post(
            "/api/products",
            json=self.generate_product_data(),
            headers=self.auth_headers(),
            name="/api/products (POST)"
        )
        if response.status_code in [200, 201]:
            try:
                product_id = response.json().get("id")
                if product_id:
                    self.created_product_ids.append(product_id)
            except:
                pass

    @task(2)
    def update_product(self):
        """PUT /api/products/{id} - обновление товара."""
        if not self.ensure_logged_in():
            return
        if self.created_product_ids:
            product_id = random.choice(self.created_product_ids)
            self.client.put(
                f"/api/products/{product_id}",
                json=self.generate_product_data(),
                headers=self.auth_headers(),
                name="/api/products/[id] (PUT)"
            )

    @task(1)
    def delete_product(self):
        """DELETE /api/products/{id} - удаление товара."""
        if not self.ensure_logged_in():
            return
        if self.created_product_ids:
            product_id = self.created_product_ids.pop()
            self.client.delete(
                f"/api/products/{product_id}",
                headers=self.auth_headers(),
                name="/api/products/[id] (DELETE)"
            )


class AdminUser(WarehouseUser):
    """ADMIN - администратор (только просмотр в текущей конфигурации API)."""
    weight = 2
    username = "admin"
    password = "password123"
    role = "admin"
    abstract = False


class ManagerUser(WarehouseUser):
    """MANAGER - менеджер склада (только просмотр в текущей конфигурации API)."""
    weight = 3
    username = "manager"
    password = "password123"
    role = "manager"
    abstract = False


class EmployeeUser(WarehouseUser):
    """EMPLOYEE - сотрудник склада (может создавать товары)."""
    weight = 5
    username = "employee"
    password = "password123"
    role = "employee"
    abstract = False

    @task(3)
    def create_product(self):
        """POST /api/products - создание товара."""
        if not self.ensure_logged_in():
            return
        response = self.client.post(
            "/api/products",
            json=self.generate_product_data(),
            headers=self.auth_headers(),
            name="/api/products (POST)"
        )
        if response.status_code in [200, 201]:
            try:
                product_id = response.json().get("id")
                if product_id:
                    self.created_product_ids.append(product_id)
            except:
                pass


class StepLoadShape(LoadTestShape):
    """
    Step-load профиль для поиска максимума.
    После оптимизации ожидаем лучшие результаты!
    """

    stages = [
        # Фаза 1: Разогрев
        {"duration": 300, "users": 10, "spawn_rate": 5},
        {"duration": 600, "users": 25, "spawn_rate": 5},
        {"duration": 900, "users": 50, "spawn_rate": 10},
        {"duration": 1200, "users": 100, "spawn_rate": 15},
        {"duration": 1500, "users": 150, "spawn_rate": 20},
        {"duration": 1800, "users": 200, "spawn_rate": 20},
        {"duration": 2100, "users": 250, "spawn_rate": 20},
        {"duration": 2400, "users": 300, "spawn_rate": 25},
        {"duration": 2700, "users": 350, "spawn_rate": 25},
        {"duration": 3000, "users": 400, "spawn_rate": 25},
        {"duration": 3300, "users": 450, "spawn_rate": 25},
        {"duration": 3600, "users": 500, "spawn_rate": 30},
        # Фаза 2: Стресс
        {"duration": 3720, "users": 650, "spawn_rate": 50},
        {"duration": 3840, "users": 800, "spawn_rate": 50},
        {"duration": 3960, "users": 950, "spawn_rate": 50},
        {"duration": 4080, "users": 1100, "spawn_rate": 50},
        {"duration": 4200, "users": 1250, "spawn_rate": 50},
        {"duration": 4320, "users": 1400, "spawn_rate": 50},
        {"duration": 4440, "users": 1550, "spawn_rate": 50},
        {"duration": 4560, "users": 1700, "spawn_rate": 50},
        {"duration": 4680, "users": 1850, "spawn_rate": 50},
        {"duration": 4800, "users": 2000, "spawn_rate": 50},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None
