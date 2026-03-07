"""
Конфигурация робота-симулятора склада.
Все настройки можно переопределить через переменные окружения с префиксом ROBOT_.
"""
from pydantic_settings import BaseSettings
from typing import Tuple


class Settings(BaseSettings):
    """Настройки робота."""

    # Warehouse API URLs для разных окружений
    api_url_home: str = "http://api:8080"
    api_url_prod: str = "https://api.wh-lab.ru"

    # Текущий URL (для обратной совместимости)
    api_url: str = "http://api:8080"

    # Окружение по умолчанию
    default_environment: str = "home"

    # Учётные данные пользователей
    employee_username: str = "admin"
    employee_password: str = "admin123"
    manager_username: str = "admin"
    manager_password: str = "admin123"
    superuser_username: str = "admin"
    superuser_password: str = "admin123"

    # Скорости выполнения сценариев (min, max секунд между действиями)
    speed_slow: Tuple[float, float] = (5.0, 10.0)
    speed_normal: Tuple[float, float] = (2.0, 5.0)
    speed_fast: Tuple[float, float] = (0.5, 2.0)

    # Telegram Bot для уведомлений
    telegram_bot_url: str = "http://telegram-bot:8000"

    # Uplink Bot для уведомлений в Matrix
    uplink_bot_url: str = ""

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
    return settings.api_url_home
