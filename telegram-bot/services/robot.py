# -*- coding: utf-8 -*-
"""
Сервис для работы с Warehouse Robot API.
"""

import httpx
import logging
from typing import Optional, Dict, Any, List

from config import ROBOT_API_URL

logger = logging.getLogger(__name__)


class RobotService:
    """Клиент для Warehouse Robot API."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or ROBOT_API_URL
        self.timeout = 30.0

    def _get_client(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout)

    def get_info(self) -> Optional[Dict[str, Any]]:
        """Получить информацию о роботе."""
        try:
            with self._get_client() as client:
                response = client.get(f"{self.base_url}/")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Robot info error: {e}")
        return None

    def get_health(self) -> Optional[Dict[str, Any]]:
        """Проверить здоровье робота."""
        try:
            with self._get_client() as client:
                response = client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Robot health error: {e}")
        return None

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Получить текущий статус робота."""
        try:
            with self._get_client() as client:
                response = client.get(f"{self.base_url}/status")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Robot status error: {e}")
        return None

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Получить статистику выполнения."""
        try:
            with self._get_client() as client:
                response = client.get(f"{self.base_url}/stats")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Robot stats error: {e}")
        return None

    def get_scenarios(self) -> List[Dict[str, Any]]:
        """Получить список сценариев."""
        try:
            with self._get_client() as client:
                response = client.get(f"{self.base_url}/scenarios")
                if response.status_code == 200:
                    return response.json().get("scenarios", [])
        except Exception as e:
            logger.error(f"Robot scenarios error: {e}")
        return []

    def start_scenario(
        self, scenario: str, speed: str = "normal", environment: str = "staging", duration: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Запустить сценарий.

        Args:
            scenario: Название сценария (receiving, shipping, inventory)
            speed: Скорость выполнения (slow=15с пауза, normal=5с пауза, fast=1с пауза)
            environment: Окружение (staging или prod)
            duration: Продолжительность повторения в минутах (0 = один раз)

        Returns:
            Результат запуска или None при ошибке
        """
        try:
            with self._get_client() as client:
                response = client.post(
                    f"{self.base_url}/start",
                    json={
                        "scenario": scenario,
                        "speed": speed,
                        "environment": environment,
                        "duration": duration,
                    }
                )
                return response.json()
        except Exception as e:
            logger.error(f"Robot start error: {e}")
        return None

    def stop(self) -> Optional[Dict[str, Any]]:
        """Остановить робота."""
        try:
            with self._get_client() as client:
                response = client.post(f"{self.base_url}/stop")
                return response.json()
        except Exception as e:
            logger.error(f"Robot stop error: {e}")
        return None

    def schedule_scenario(
        self, scenario: str, scheduled_time: str, speed: str = "normal", environment: str = "staging"
    ) -> Optional[Dict[str, Any]]:
        """
        Запланировать сценарий на указанное время.

        Args:
            scenario: Название сценария (receiving, shipping, inventory)
            scheduled_time: Время запуска (HH:MM или ISO datetime)
            speed: Скорость выполнения (slow, normal, fast)
            environment: Окружение (staging или prod)

        Returns:
            Результат планирования или None при ошибке
        """
        try:
            with self._get_client() as client:
                response = client.post(
                    f"{self.base_url}/schedule",
                    json={
                        "scenario": scenario,
                        "scheduled_time": scheduled_time,
                        "speed": speed,
                        "environment": environment,
                    }
                )
                return response.json()
        except Exception as e:
            logger.error(f"Robot schedule error: {e}")
        return None

    def get_scheduled(self) -> List[Dict[str, Any]]:
        """Получить список запланированных задач."""
        try:
            with self._get_client() as client:
                response = client.get(f"{self.base_url}/scheduled")
                if response.status_code == 200:
                    return response.json().get("scheduled_tasks", [])
        except Exception as e:
            logger.error(f"Robot scheduled error: {e}")
        return []

    def cancel_scheduled(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Отменить запланированную задачу."""
        try:
            with self._get_client() as client:
                response = client.delete(f"{self.base_url}/scheduled/{task_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Robot cancel error: {e}")
        return None

    def is_available(self) -> bool:
        """Проверить доступность робота."""
        health = self.get_health()
        return health is not None and health.get("status") == "ok"


# Глобальный экземпляр сервиса
robot_service = RobotService()
