"""
Конфигурация робота-симулятора склада.
Все настройки можно переопределить через переменные окружения с префиксом ROBOT_.
"""
from pydantic_settings import BaseSettings
from typing import Tuple


class Settings(BaseSettings):
    """Настройки робота."""

    # Warehouse API URLs для разных окружений
    api_url_staging: str = "http://warehouse-api-service.warehouse.svc.cluster.local:8080"
    api_url_prod: str = "https://api.wh-lab.ru"

    # Текущий URL (для обратной совместимости)
    api_url: str = "http://warehouse-api-service.warehouse.svc.cluster.local:8080"

    # Окружение по умолчанию
    default_environment: str = "staging"

    # Учётные данные пользователей
    # WH-174: Пароли читаются из env (K8s Secret), defaults для локальной разработки
    employee_username: str = "employee"
    employee_password: str = "password123"  # ROBOT_EMPLOYEE_PASSWORD в prod
    manager_username: str = "manager"
    manager_password: str = "password123"   # ROBOT_MANAGER_PASSWORD в prod
    superuser_username: str = "superuser"
    superuser_password: str = "password123" # ROBOT_SUPERUSER_PASSWORD в prod

    # Скорости выполнения сценариев (min, max секунд между действиями)
    speed_slow: Tuple[float, float] = (5.0, 10.0)
    speed_normal: Tuple[float, float] = (2.0, 5.0)
    speed_fast: Tuple[float, float] = (0.5, 2.0)

    # Telegram Bot для уведомлений
    telegram_bot_url: str = "http://gitlab-telegram-bot.notifications.svc.cluster.local:8000"

    # Порт API робота
    api_port: int = 8070

    # WH-179: Таймауты HTTP запросов (секунды)
    api_timeout: float = 30.0       # Таймаут для CRUD операций
    health_timeout: float = 5.0     # Таймаут для health check

    class Config:
        env_prefix = "ROBOT_"
        env_file = ".env"
        env_file_encoding = "utf-8"


# Глобальный экземпляр настроек
settings = Settings()


def get_api_url(environment: str = None) -> str:
    """
    Получить URL API для указанного окружения.

    Args:
        environment: Окружение (staging/prod). Если None - используется default.

    Returns:
        URL Warehouse API
    """
    env = environment or settings.default_environment
    if env == "prod":
        return settings.api_url_prod
    return settings.api_url_staging
