"""
Базовый класс для всех сценариев работы склада.
"""
import random
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

from api_client import WarehouseAPIClient
from config import settings

logger = logging.getLogger(__name__)


class BaseScenario(ABC):
    """Базовый класс сценария складской операции."""

    # Название сценария (переопределить в наследниках)
    name: str = "base"
    description: str = "Базовый сценарий"

    def __init__(self, client: WarehouseAPIClient, speed: str = "normal"):
        """
        Инициализация сценария.

        Args:
            client: Клиент API склада
            speed: Скорость выполнения (slow, normal, fast)
        """
        self.client = client
        self.speed = speed
        self.stats = {
            "actions": 0,
            "products_created": 0,
            "products_updated": 0,
            "products_deleted": 0,
            "errors": 0,
        }

    def get_delay(self) -> float:
        """
        Получить случайную задержку в зависимости от скорости.

        Returns:
            Задержка в секундах
        """
        delays = {
            "slow": settings.speed_slow,
            "normal": settings.speed_normal,
            "fast": settings.speed_fast,
        }
        min_delay, max_delay = delays.get(self.speed, settings.speed_normal)
        return random.uniform(min_delay, max_delay)

    def wait(self):
        """Подождать между действиями для реалистичности."""
        delay = self.get_delay()
        logger.debug(f"⏳ Ожидание {delay:.1f} сек...")
        time.sleep(delay)

    def log_action(self, message: str):
        """Логирование действия с инкрементом счётчика."""
        logger.info(message)
        self.stats["actions"] += 1

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """
        Выполнить сценарий.

        Returns:
            Словарь с результатами выполнения и статистикой
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику выполнения.

        Returns:
            Словарь со статистикой
        """
        return self.stats.copy()
