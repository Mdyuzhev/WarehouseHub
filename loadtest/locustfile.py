"""
=============================================================================
Сценарий нагрузочного тестирования для Warehouse API
=============================================================================

WH-185: Унифицированный locustfile для всех окружений

Описание:
    Единый сценарий нагрузочного тестирования с поддержкой:
    - 4 типа пользователей (SuperUser, Admin, Manager, Employee)
    - Кэширование JWT токенов для снижения нагрузки BCrypt
    - 2 профиля нагрузки (LinearLoadShape, StepLoadShape)

Профили нагрузки:
    - LinearLoadShape: плавный рост 0 -> 100 за 10 мин + удержание 5 мин
    - StepLoadShape: ступенчатый рост до 2000 пользователей для стресс-теста

Типы пользователей и их веса:
    - SuperUser (10%): полный доступ - CRUD + управление
    - AdminUser (20%): администратор - только просмотр
    - ManagerUser (30%): менеджер - только просмотр
    - EmployeeUser (50%): сотрудник - просмотр + создание товаров

Запуск локально:
    locust -f locustfile.py --host=http://localhost:8080

Запуск в headless режиме:
    locust -f locustfile.py --host=http://localhost:8080 \
           --headless -u 100 -r 10 --run-time 15m

Веб-интерфейс:
    После запуска открыть http://localhost:8089

Переменные окружения (см. .env.example):
    LOCUST_SUPERUSER_PASSWORD, LOCUST_ADMIN_PASSWORD,
    LOCUST_MANAGER_PASSWORD, LOCUST_EMPLOYEE_PASSWORD

=============================================================================
"""

import os
import random
import string
import time
import threading
from locust import HttpUser, task, between
from locust import LoadTestShape

# =============================================================================
# Конфигурация из переменных окружения
# =============================================================================
SUPERUSER_PASSWORD = os.getenv("LOCUST_SUPERUSER_PASSWORD", "password123")
ADMIN_PASSWORD = os.getenv("LOCUST_ADMIN_PASSWORD", "password123")
MANAGER_PASSWORD = os.getenv("LOCUST_MANAGER_PASSWORD", "password123")
EMPLOYEE_PASSWORD = os.getenv("LOCUST_EMPLOYEE_PASSWORD", "password123")

# Категории товаров для тестов
CATEGORIES = ["Электроника", "Одежда", "Продукты", "Инструменты", "Бытовая техника"]

# =============================================================================
# Глобальный кэш токенов
# =============================================================================
# Токен получаем 1 раз на роль, переиспользуем для всех users этой роли
# Это значительно снижает нагрузку на BCrypt при массовой авторизации
TOKEN_CACHE = {}
TOKEN_CACHE_LOCK = threading.Lock()


# =============================================================================
# Базовый класс пользователя
# =============================================================================
class WarehouseUser(HttpUser):
    """
    Базовый класс пользователя склада.

    Содержит общую логику для всех типов пользователей:
    - Авторизация с кэшированием токенов и retry-механизмом
    - Управление JWT токеном
    - Очистка созданных данных при завершении
    - Общие задачи (просмотр товаров, профиля)

    Attributes:
        wait_time: Пауза между запросами (1-3 секунды)
        username: Логин пользователя (переопределяется в подклассах)
        password: Пароль пользователя (переопределяется в подклассах)
        role: Роль для идентификации в логах
        abstract: True = не создавать экземпляры этого класса напрямую
    """

    # Пауза между запросами - имитирует "думание" пользователя
    wait_time = between(1, 3)

    # Учётные данные (переопределяются в подклассах)
    username = None
    password = None
    role = None

    # Абстрактный класс - не создавать экземпляры напрямую
    abstract = True

    # -------------------------------------------------------------------------
    # Lifecycle методы
    # -------------------------------------------------------------------------

    def on_start(self):
        """
        Вызывается при старте каждого виртуального пользователя.
        Инициализирует состояние и выполняет авторизацию с кэшированием.
        """
        self.token = None
        self.created_product_ids = []
        self.login_with_cache()

    def on_stop(self):
        """
        Вызывается при остановке виртуального пользователя.
        Удаляет все продукты, созданные этим пользователем.
        """
        for product_id in self.created_product_ids:
            try:
                self.client.delete(
                    f"/api/products/{product_id}",
                    headers=self.auth_headers(),
                    name="/api/products/[id] (cleanup)"
                )
            except:
                pass

    # -------------------------------------------------------------------------
    # Методы авторизации
    # -------------------------------------------------------------------------

    def login_with_cache(self):
        """
        Логин с кэшированием токена по роли.

        Сначала проверяет глобальный кэш токенов.
        Если токен есть - использует его без HTTP запроса.
        Если нет - выполняет реальный логин и сохраняет в кэш.

        Returns:
            bool: True если авторизация успешна
        """
        cache_key = self.username

        # Проверяем кэш (thread-safe)
        with TOKEN_CACHE_LOCK:
            if cache_key in TOKEN_CACHE:
                self.token = TOKEN_CACHE[cache_key]
                return True

        # Токена нет в кэше — делаем реальный логин
        return self.login_with_retry()

    def login_with_retry(self, max_retries=3):
        """
        Выполняет авторизацию с повторными попытками.

        При высокой нагрузке сервер может временно не отвечать,
        поэтому делаем несколько попыток с экспоненциальной задержкой.
        Успешный токен сохраняется в глобальный кэш.

        Args:
            max_retries: Максимальное количество попыток (по умолчанию 3)

        Returns:
            bool: True если авторизация успешна, False иначе
        """
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
            except:
                pass

            # Экспоненциальная задержка: 0.5s, 1s, 1.5s
            time.sleep(0.5 * (attempt + 1))

        return False

    def ensure_logged_in(self):
        """
        Проверяет наличие токена и при необходимости повторно авторизуется.

        Returns:
            bool: True если пользователь авторизован
        """
        if not self.token:
            return self.login_with_cache()
        return True

    def auth_headers(self):
        """
        Возвращает заголовки авторизации для HTTP запросов.

        Returns:
            dict: {"Authorization": "Bearer <token>"} или пустой словарь
        """
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # -------------------------------------------------------------------------
    # Вспомогательные методы
    # -------------------------------------------------------------------------

    def generate_product_name(self):
        """
        Генерирует уникальное имя продукта для тестов.

        Формат: "LoadTest-{role}-{random_suffix}"
        Пример: "LoadTest-employee-a1b2c3d4"

        Returns:
            str: Уникальное имя продукта
        """
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"LoadTest-{self.role}-{suffix}"

    def generate_product_data(self):
        """
        Генерация полных данных продукта с description и category.

        Returns:
            dict: Данные продукта для POST/PUT запросов
        """
        return {
            "name": self.generate_product_name(),
            "quantity": random.randint(1, 100),
            "price": round(random.uniform(10.0, 1000.0), 2),
            "description": f"Тестовый товар от {self.role}",
            "category": random.choice(CATEGORIES)
        }

    # -------------------------------------------------------------------------
    # Общие задачи для всех пользователей
    # -------------------------------------------------------------------------

    @task(5)
    def view_products(self):
        """
        GET /api/products - просмотр списка всех продуктов.

        Это самая частая операция - пользователи постоянно
        смотрят что есть на складе.

        Weight: 5 (выполняется в 5 раз чаще чем task с weight=1)
        """
        if not self.ensure_logged_in():
            return
        self.client.get(
            "/api/products",
            headers=self.auth_headers(),
            name="/api/products (GET)"
        )

    @task(2)
    def view_products_by_category(self):
        """
        GET /api/products?category=... - фильтрация по категории.

        Weight: 2
        """
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
        """
        GET /api/auth/me - информация о текущем пользователе.

        Редкая операция - обычно делается один раз при входе.

        Weight: 1 (базовая частота)
        """
        if not self.ensure_logged_in():
            return
        self.client.get(
            "/api/auth/me",
            headers=self.auth_headers(),
            name="/api/auth/me"
        )


# =============================================================================
# SuperUser - полный доступ
# =============================================================================
class SuperUser(WarehouseUser):
    """
    SUPER_USER - полный доступ ко всему.

    Может выполнять все операции: создание, чтение, обновление, удаление.
    Составляет 10% от общей нагрузки (weight=1).
    """

    weight = 1
    username = "superuser"
    password = SUPERUSER_PASSWORD
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


# =============================================================================
# AdminUser - администратор
# =============================================================================
class AdminUser(WarehouseUser):
    """
    ADMIN - администратор (только просмотр в текущей конфигурации API).

    Составляет 20% от общей нагрузки (weight=2).
    """

    weight = 2
    username = "admin"
    password = ADMIN_PASSWORD
    role = "admin"
    abstract = False


# =============================================================================
# ManagerUser - менеджер
# =============================================================================
class ManagerUser(WarehouseUser):
    """
    MANAGER - менеджер склада (только просмотр).

    Составляет 30% от общей нагрузки (weight=3).
    Менеджеры чаще смотрят отчёты и статистику.
    """

    weight = 3
    username = "manager"
    password = MANAGER_PASSWORD
    role = "manager"
    abstract = False

    @task(3)
    def view_products_detailed(self):
        """
        Детальный просмотр списка продуктов.

        Менеджеры чаще смотрят отчёты, поэтому добавляем
        дополнительную задачу просмотра.
        """
        if not self.ensure_logged_in():
            return
        self.client.get(
            "/api/products",
            headers=self.auth_headers(),
            name="/api/products (GET)"
        )


# =============================================================================
# EmployeeUser - сотрудник склада
# =============================================================================
class EmployeeUser(WarehouseUser):
    """
    EMPLOYEE - сотрудник склада (может создавать товары).

    Составляет 50% от общей нагрузки (weight=5).
    Основной тип пользователя системы.
    """

    weight = 5
    username = "employee"
    password = EMPLOYEE_PASSWORD
    role = "employee"
    abstract = False

    @task(3)
    def create_product(self):
        """
        POST /api/products - создание нового продукта на складе.

        Сохраняет ID созданного продукта для последующей очистки.
        """
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
    def delete_own_product(self):
        """
        DELETE /api/products/{id} - удаление ранее созданного продукта.

        Удаляет один из продуктов, созданных этим же пользователем.
        """
        if not self.ensure_logged_in():
            return

        if self.created_product_ids:
            product_id = self.created_product_ids.pop()
            self.client.delete(
                f"/api/products/{product_id}",
                headers=self.auth_headers(),
                name="/api/products/[id] (DELETE)"
            )


# =============================================================================
# Профили нагрузки
# =============================================================================

class LinearLoadShape(LoadTestShape):
    """
    Линейный профиль нагрузки.

    Плавно увеличивает количество пользователей от 0 до target_users
    за время ramp_time, затем удерживает нагрузку hold_time.

    Временная шкала (при настройках по умолчанию):
        0:00 - 10:00  -> Линейный рост 0 -> 100 пользователей
        10:00 - 15:00 -> Удержание на 100 пользователях
        15:00         -> Завершение теста

    Использование:
        Раскомментируйте этот класс для плавного теста.
    """

    target_users = 100   # Максимум пользователей
    ramp_time = 600      # 10 минут на разгон (600 секунд)
    hold_time = 300      # 5 минут на пике (300 секунд)
    spawn_rate = 10      # Добавлять по 10 пользователей в секунду

    def tick(self):
        """Определяет количество пользователей в текущий момент времени."""
        run_time = self.get_run_time()
        total_time = self.ramp_time + self.hold_time

        if run_time > total_time:
            return None

        if run_time < self.ramp_time:
            current_users = int((run_time / self.ramp_time) * self.target_users)
            return (max(1, current_users), self.spawn_rate)
        else:
            return (self.target_users, self.spawn_rate)


class StepLoadShape(LoadTestShape):
    """
    Ступенчатый профиль нагрузки для стресс-тестирования.

    Постепенно увеличивает нагрузку ступенями для поиска точки отказа.
    Используется для A/B тестирования и определения максимальной нагрузки.

    Фазы:
        1. Разогрев: 10 -> 500 пользователей (плавно)
        2. Стресс: 650 -> 2000 пользователей (агрессивно)

    Использование:
        Закомментируйте LinearLoadShape и раскомментируйте этот класс.
    """

    stages = [
        # Фаза 1: Разогрев (0-60 минут)
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
        # Фаза 2: Стресс (60-80 минут)
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
        """Определяет количество пользователей по текущей ступени."""
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None
