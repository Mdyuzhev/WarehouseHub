"""
HTTP клиент для работы с Warehouse API.
Обеспечивает авторизацию через JWT и CRUD операции с товарами.
"""
import httpx
import logging
from typing import Optional, List, Dict, Any

from config import settings

logger = logging.getLogger(__name__)


class WarehouseAPIClient:
    """Клиент для работы с Warehouse API."""

    def __init__(self, base_url: str = None):
        """
        Инициализация клиента.

        Args:
            base_url: URL Warehouse API. По умолчанию из настроек.
        """
        self.base_url = base_url or settings.api_url
        self.token: Optional[str] = None
        self.username: Optional[str] = None
        # WH-179: таймаут из конфига
        self.client = httpx.Client(timeout=settings.api_timeout)

    def login(self, username: str = None, password: str = None) -> bool:
        """
        Авторизация в системе, получение JWT токена.

        Args:
            username: Имя пользователя. По умолчанию из настроек.
            password: Пароль. По умолчанию из настроек.

        Returns:
            True если авторизация успешна, False иначе
        """
        # Используем значения по умолчанию из настроек
        username = username or settings.employee_username
        password = password or settings.employee_password

        try:
            response = self.client.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "password": password}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.username = username
                logger.info(f"✅ Авторизация успешна: {username}")
                return True
            else:
                logger.error(f"❌ Ошибка авторизации {username}: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Исключение при авторизации: {e}")
            return False

    def _headers(self) -> Dict[str, str]:
        """
        Формирование заголовков запроса с авторизацией.

        Returns:
            Словарь заголовков
        """
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_products(self, category: str = None) -> List[Dict[str, Any]]:
        """
        Получить список товаров.

        Args:
            category: Фильтр по категории (опционально)

        Returns:
            Список товаров
        """
        try:
            url = f"{self.base_url}/api/products"
            if category:
                url += f"?category={category}"

            response = self.client.get(url, headers=self._headers())

            if response.status_code == 200:
                products = response.json()
                logger.debug(f"📦 Получено товаров: {len(products)}")
                return products
            else:
                logger.warning(f"⚠️ Ошибка получения товаров: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Исключение при получении товаров: {e}")
            return []

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить один товар по ID.

        Args:
            product_id: ID товара

        Returns:
            Данные товара или None
        """
        try:
            response = self.client.get(
                f"{self.base_url}/api/products/{product_id}",
                headers=self._headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"⚠️ Товар {product_id} не найден: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Исключение при получении товара {product_id}: {e}")
            return None

    def create_product(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Создать новый товар.

        Args:
            product: Данные товара (name, category, quantity, price, description)

        Returns:
            Созданный товар или None при ошибке
        """
        try:
            response = self.client.post(
                f"{self.base_url}/api/products",
                json=product,
                headers=self._headers()
            )

            if response.status_code in [200, 201]:
                created = response.json()
                logger.info(f"✅ Товар создан: {created.get('id')} - {product.get('name')}")
                return created
            else:
                logger.error(f"❌ Ошибка создания товара: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Исключение при создании товара: {e}")
            return None

    def update_product(self, product_id: int, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Обновить товар.

        Args:
            product_id: ID товара
            product: Новые данные товара

        Returns:
            Обновлённый товар или None при ошибке
        """
        try:
            response = self.client.put(
                f"{self.base_url}/api/products/{product_id}",
                json=product,
                headers=self._headers()
            )

            if response.status_code == 200:
                updated = response.json()
                logger.info(f"✅ Товар обновлён: {product_id}")
                return updated
            else:
                logger.error(f"❌ Ошибка обновления товара {product_id}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Исключение при обновлении товара {product_id}: {e}")
            return None

    def delete_product(self, product_id: int) -> bool:
        """
        Удалить товар.

        Args:
            product_id: ID товара

        Returns:
            True если удаление успешно, False иначе
        """
        try:
            response = self.client.delete(
                f"{self.base_url}/api/products/{product_id}",
                headers=self._headers()
            )

            if response.status_code in [200, 204]:
                logger.info(f"🗑️ Товар удалён: {product_id}")
                return True
            else:
                logger.error(f"❌ Ошибка удаления товара {product_id}: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Исключение при удалении товара {product_id}: {e}")
            return False

    def health_check(self) -> bool:
        """
        Проверка доступности API.

        Returns:
            True если API доступен, False иначе
        """
        try:
            # WH-179: таймаут из конфига
            response = self.client.get(f"{self.base_url}/actuator/health", timeout=settings.health_timeout)
            return response.status_code == 200

        except Exception:
            return False

    def close(self):
        """Закрыть HTTP соединение."""
        self.client.close()
        logger.debug("🔌 Соединение закрыто")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
