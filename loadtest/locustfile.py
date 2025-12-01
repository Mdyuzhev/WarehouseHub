"""
=============================================================================
Сценарий нагрузочного тестирования для Warehouse API
=============================================================================

Описание:
    Этот файл содержит сценарии нагрузочного тестирования с использованием
    фреймворка Locust. Имитирует реальное поведение пользователей склада.

Профиль нагрузки:
    - Линейный рост: 0 -> 100 пользователей за 10 минут
    - Удержание на пике: 5 минут при 100 пользователях
    - Общая длительность: 15 минут

Типы пользователей:
    - EmployeeUser (70%): сотрудники склада - создают/удаляют продукты
    - ManagerUser (30%): менеджеры - только просмотр данных

Запуск локально:
    locust -f locustfile.py --host=http://localhost:8080

Запуск в headless режиме:
    locust -f locustfile.py --host=http://localhost:8080 \
           --headless -u 100 -r 10 --run-time 15m

Веб-интерфейс:
    После запуска открыть http://localhost:8089

WH-177: Credentials вынесены в переменные окружения
=============================================================================
"""

import os
import random
import string
import time
from locust import HttpUser, task, between
from locust import LoadTestShape

# =============================================================================
# WH-177: Конфигурация из переменных окружения
# =============================================================================
EMPLOYEE_PASSWORD = os.getenv("LOCUST_EMPLOYEE_PASSWORD", "employee123")
MANAGER_PASSWORD = os.getenv("LOCUST_MANAGER_PASSWORD", "manager123")


# =============================================================================
# Базовый класс пользователя
# =============================================================================

class WarehouseUser(HttpUser):
    """
    Базовый класс пользователя склада.

    Содержит общую логику для всех типов пользователей:
    - Авторизация с retry-механизмом
    - Управление JWT токеном
    - Очистка созданных данных при завершении

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
        Инициализирует состояние и выполняет авторизацию.
        """
        self.token = None                    # JWT токен авторизации
        self.created_product_ids = []        # ID созданных продуктов (для очистки)
        self.login_with_retry()              # Авторизуемся сразу при старте

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
                    name="/api/products/[id] (cleanup)"  # Группируем в статистике
                )
            except:
                pass  # Игнорируем ошибки при очистке

    # -------------------------------------------------------------------------
    # Методы авторизации
    # -------------------------------------------------------------------------

    def login_with_retry(self, max_retries=3):
        """
        Выполняет авторизацию с повторными попытками.

        При высокой нагрузке сервер может временно не отвечать,
        поэтому делаем несколько попыток с экспоненциальной задержкой.

        Args:
            max_retries: Максимальное количество попыток (по умолчанию 3)

        Returns:
            bool: True если авторизация успешна, False иначе
        """
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
                        return True
            except:
                pass  # Сетевая ошибка - пробуем ещё раз

            # Экспоненциальная задержка: 0.5s, 1s, 1.5s
            time.sleep(0.5 * (attempt + 1))

        return False

    def ensure_logged_in(self):
        """
        Проверяет наличие токена и при необходимости повторно авторизуется.

        Вызывается перед каждым защищённым запросом.

        Returns:
            bool: True если пользователь авторизован
        """
        if not self.token:
            self.login_with_retry()
        return self.token is not None

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

    # -------------------------------------------------------------------------
    # Общие задачи для всех пользователей
    # -------------------------------------------------------------------------

    @task(5)  # Weight=5: самая частая операция
    def view_products(self):
        """
        Просмотр списка всех продуктов.

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

    @task(1)  # Weight=1: редкая операция
    def view_current_user(self):
        """
        Просмотр информации о текущем пользователе.

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
# Класс сотрудника склада
# =============================================================================

class EmployeeUser(WarehouseUser):
    """
    Сотрудник склада - основной тип пользователя.

    Может выполнять все операции: просмотр, создание, удаление продуктов.
    Составляет 70% от общей нагрузки (weight=7).

    Распределение задач:
        - view_products: 5 (просмотр списка)
        - create_product: 3 (создание продукта)
        - delete_own_product: 2 (удаление продукта)
        - view_current_user: 1 (информация о себе)
    """

    # 70% от общего количества пользователей
    weight = 7

    # Учётные данные сотрудника (WH-177: из env)
    username = "employee"
    password = EMPLOYEE_PASSWORD
    role = "employee"

    # Это конкретный класс - создавать экземпляры
    abstract = False

    @task(3)  # Weight=3: частая операция
    def create_product(self):
        """
        Создание нового продукта на складе.

        Генерирует случайные данные продукта и отправляет POST запрос.
        Сохраняет ID созданного продукта для последующей очистки.

        Weight: 3 (достаточно частая операция)
        """
        if not self.ensure_logged_in():
            return

        # Генерируем случайные данные продукта
        product_name = self.generate_product_name()
        response = self.client.post(
            "/api/products",
            json={
                "name": product_name,
                "quantity": random.randint(1, 100),        # 1-100 единиц
                "price": round(random.uniform(10.0, 500.0), 2)  # 10-500 руб
            },
            headers=self.auth_headers(),
            name="/api/products (POST)"
        )

        # Сохраняем ID для последующего удаления
        if response.status_code in [200, 201]:
            try:
                product_id = response.json().get("id")
                if product_id:
                    self.created_product_ids.append(product_id)
            except:
                pass

    @task(2)  # Weight=2: менее частая операция
    def delete_own_product(self):
        """
        Удаление ранее созданного продукта.

        Удаляет один из продуктов, созданных этим же пользователем.
        Это позволяет не засорять базу данных во время тестов.

        Weight: 2 (реже чем создание, чтобы база немного росла)
        """
        if not self.ensure_logged_in():
            return

        # Удаляем только если есть что удалять
        if self.created_product_ids:
            product_id = self.created_product_ids.pop()
            self.client.delete(
                f"/api/products/{product_id}",
                headers=self.auth_headers(),
                name="/api/products/[id] (DELETE)"
            )


# =============================================================================
# Класс менеджера
# =============================================================================

class ManagerUser(WarehouseUser):
    """
    Менеджер - пользователь только для чтения.

    Может только просматривать данные, не может создавать/удалять.
    Составляет 30% от общей нагрузки (weight=3).

    Распределение задач:
        - view_products: 5 (просмотр списка, унаследовано)
        - view_products_detailed: 3 (дополнительный просмотр)
        - view_current_user: 1 (информация о себе, унаследовано)
    """

    # 30% от общего количества пользователей
    weight = 3

    # Учётные данные менеджера (WH-177: из env)
    username = "manager"
    password = MANAGER_PASSWORD
    role = "manager"

    # Это конкретный класс - создавать экземпляры
    abstract = False

    @task(3)
    def view_products_detailed(self):
        """
        Детальный просмотр списка продуктов.

        Менеджеры чаще смотрят отчёты, поэтому добавляем
        дополнительную задачу просмотра.

        Weight: 3 (дополнительно к унаследованной view_products)
        """
        if not self.ensure_logged_in():
            return
        self.client.get(
            "/api/products",
            headers=self.auth_headers(),
            name="/api/products (GET)"
        )


# =============================================================================
# Профиль нагрузки
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

    Attributes:
        target_users: Целевое количество пользователей (100)
        ramp_time: Время разгона в секундах (600 = 10 минут)
        hold_time: Время удержания в секундах (300 = 5 минут)
        spawn_rate: Скорость добавления пользователей (10/сек)
    """

    # Конфигурация профиля
    target_users = 100   # Максимум пользователей
    ramp_time = 600      # 10 минут на разгон (600 секунд)
    hold_time = 300      # 5 минут на пике (300 секунд)
    spawn_rate = 10      # Добавлять по 10 пользователей в секунду

    def tick(self):
        """
        Определяет количество пользователей в текущий момент времени.

        Вызывается Locust каждую секунду для определения нагрузки.

        Returns:
            tuple: (количество_пользователей, spawn_rate) или None для остановки
        """
        run_time = self.get_run_time()
        total_time = self.ramp_time + self.hold_time

        # Тест завершён
        if run_time > total_time:
            return None

        # Фаза разгона: линейный рост
        if run_time < self.ramp_time:
            # Формула: текущие = (прошло_времени / время_разгона) * целевые
            current_users = int((run_time / self.ramp_time) * self.target_users)
            return (max(1, current_users), self.spawn_rate)

        # Фаза удержания: постоянная нагрузка
        else:
            return (self.target_users, self.spawn_rate)
