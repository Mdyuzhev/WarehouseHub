"""
WebSocket Manager for Real-time Updates.
WH-121: Управление WebSocket соединениями.
"""

import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Менеджер WebSocket соединений."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Принимает новое WebSocket соединение."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Отключает WebSocket соединение."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Отправляет сообщение всем подключённым клиентам.

        Args:
            message: Сообщение для отправки
        """
        if not self.active_connections:
            return

        message_json = json.dumps(message, default=str)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message: {e}")
                disconnected.append(connection)

        # Удаляем отключённые соединения
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Отправляет сообщение конкретному клиенту.

        Args:
            websocket: WebSocket соединение
            message: Сообщение для отправки
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    @property
    def connection_count(self) -> int:
        """Количество активных соединений."""
        return len(self.active_connections)


# Глобальный экземпляр
manager = WebSocketManager()
