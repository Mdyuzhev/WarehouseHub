"""
Analytics Service Configuration.
WH-121: Real-time Kafka Analytics Dashboard.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Конфигурация analytics-service."""

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_group_id: str = "analytics-service"
    kafka_audit_topic: str = "warehouse.audit"
    kafka_notifications_topic: str = "warehouse.notifications"

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 1  # Отдельная БД для аналитики

    # API
    api_port: int = 8090
    api_host: str = "0.0.0.0"

    # Агрегация
    aggregation_window_seconds: int = 60  # Окно агрегации в секундах
    max_events_in_feed: int = 100  # Максимум событий в live feed
    stats_ttl_seconds: int = 86400  # TTL статистики (24 часа)

    class Config:
        env_prefix = "ANALYTICS_"
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
