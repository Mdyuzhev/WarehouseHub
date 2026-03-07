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

    def _is_configured(self) -> bool:
        return bool(self.base_url)

    def _get_client(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout)

    def get_info(self) -> Optional[Dict[str, Any]]:
        if not self._is_configured():
            return None
        try:
            with self._get_client() as client:
                response = client.get(f"{self.base_url}/")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Robot info error: {e}")
        return None

    def get_health(self) -> Optional[Dict[str, Any]]:
        if not self._is_configured():
            return None
        try:
            with self._get_client() as client:
                response = client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Robot health error: {e}")
        return None

    def get_status(self) -> Optional[Dict[str, Any]]:
        if not self._is_configured():
            return None
        try:
            with self._get_client() as client:
                response = client.get(f"{self.base_url}/status")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Robot status error: {e}")
        return None

    def get_stats(self) -> Optional[Dict[str, Any]]:
        if not self._is_configured():
            return None
        try:
            with self._get_client() as client:
                response = client.get(f"{self.base_url}/stats")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Robot stats error: {e}")
        return None

    def is_available(self) -> bool:
        health = self.get_health()
        return health is not None and health.get("status") == "ok"


robot_service = RobotService()
