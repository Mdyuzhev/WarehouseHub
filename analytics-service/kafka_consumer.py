"""
Kafka Consumer for Analytics.
WH-121: Потребление событий из Kafka.
"""

import json
import logging
import asyncio
from typing import Optional, Callable, List
from aiokafka import AIOKafkaConsumer

from config import settings
from redis_store import store

logger = logging.getLogger(__name__)


class AnalyticsConsumer:
    """Kafka Consumer для аналитики."""

    def __init__(self, on_event: Optional[Callable] = None):
        """
        Args:
            on_event: Callback для real-time уведомлений (WebSocket)
        """
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        self.on_event = on_event

    async def start(self):
        """Запуск consumer."""
        self.consumer = AIOKafkaConsumer(
            settings.kafka_audit_topic,
            settings.kafka_notifications_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_group_id,
            auto_offset_reset="latest",  # Начинаем с новых сообщений
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )

        await self.consumer.start()
        self.running = True
        logger.info(f"Kafka consumer started. Topics: {settings.kafka_audit_topic}, {settings.kafka_notifications_topic}")

    async def stop(self):
        """Остановка consumer."""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def consume(self):
        """
        Основной цикл потребления сообщений.
        Обрабатывает события и сохраняет в Redis.
        """
        try:
            async for msg in self.consumer:
                if not self.running:
                    break

                try:
                    await self.process_message(msg.topic, msg.value)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except asyncio.CancelledError:
            logger.info("Consumer cancelled")
        except Exception as e:
            logger.error(f"Consumer error: {e}")

    async def process_message(self, topic: str, data: dict):
        """
        Обработка сообщения.

        Args:
            topic: Название топика
            data: Данные сообщения
        """
        logger.debug(f"Received message from {topic}: {data}")

        if topic == settings.kafka_audit_topic:
            await self.process_audit_event(data)
        elif topic == settings.kafka_notifications_topic:
            await self.process_notification_event(data)

    async def process_audit_event(self, data: dict):
        """
        Обработка события аудита.
        Events: CREATE, UPDATE, DELETE, LOGIN, LOGOUT
        """
        event_type = data.get("eventType", "UNKNOWN")
        entity_type = data.get("entityType", "UNKNOWN")
        entity_name = data.get("entityName", "")
        username = data.get("username", "anonymous")
        timestamp = data.get("timestamp", "")

        # Формируем событие для feed
        feed_event = {
            "type": "audit",
            "event": event_type,
            "entity": entity_type,
            "name": entity_name,
            "user": username,
            "timestamp": timestamp,
            "details": data.get("details", "")
        }

        # Сохраняем в Redis
        await store.add_event(feed_event)

        # Обновляем статистику
        await store.increment_stat(f"total_{event_type.lower()}")
        await store.increment_stat("total_events")
        await store.record_hourly_event(event_type)
        await store.record_daily_event(event_type)

        # Если это продукт - обновляем категорию
        if entity_type == "PRODUCT" and "category" in str(data.get("details", "")):
            # Пытаемся извлечь категорию из details
            details = data.get("details", "")
            if "category:" in details.lower():
                # Простой парсинг category из details
                pass

        # Callback для WebSocket
        if self.on_event:
            await self.on_event(feed_event)

        logger.info(f"Processed audit event: {event_type} {entity_type} '{entity_name}' by {username}")

    async def process_notification_event(self, data: dict):
        """
        Обработка уведомления о stock.
        Events: LOW_STOCK, OUT_OF_STOCK
        """
        notification_type = data.get("notificationType", "UNKNOWN")
        product_name = data.get("productName", "")
        category = data.get("category", "unknown")
        quantity = data.get("currentQuantity", 0)
        timestamp = data.get("timestamp", "")

        # Формируем событие для feed
        feed_event = {
            "type": "notification",
            "event": notification_type,
            "name": product_name,
            "category": category,
            "quantity": quantity,
            "timestamp": timestamp,
            "message": data.get("message", "")
        }

        # Сохраняем в Redis
        await store.add_event(feed_event)

        # Обновляем статистику
        await store.increment_stat(f"total_{notification_type.lower()}")
        await store.increment_stat("total_notifications")
        await store.record_category_event(category, notification_type)

        # Callback для WebSocket
        if self.on_event:
            await self.on_event(feed_event)

        logger.info(f"Processed notification: {notification_type} for '{product_name}'")


# Глобальный экземпляр
consumer = AnalyticsConsumer()
