"""
Analytics Service Configuration.
WH-121: Real-time Kafka Analytics Dashboard.
WH-182: Документация магических чисел.

Все настройки можно переопределить через переменные окружения с префиксом ANALYTICS_.
Например: ANALYTICS_KAFKA_BOOTSTRAP_SERVERS=kafka-cluster:9092
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Конфигурация analytics-service.

    Переменные окружения:
    - ANALYTICS_KAFKA_BOOTSTRAP_SERVERS: адрес Kafka кластера
    - ANALYTICS_REDIS_HOST: адрес Redis сервера
    - ANALYTICS_AGGREGATION_WINDOW_SECONDS: окно агрегации метрик
    """

    # =========================================================================
    # Kafka Configuration
    # =========================================================================
    # Адрес Kafka брокера. В K8s используйте service name: kafka.kafka.svc.cluster.local:9092
    kafka_bootstrap_servers: str = "kafka:9092"
    # Consumer group ID для этого сервиса (уникальный для каждого сервиса)
    kafka_group_id: str = "analytics-service"
    # Топик с аудит-событиями от warehouse-api
    kafka_audit_topic: str = "warehouse.audit"
    # Топик для уведомлений (alerts, warnings)
    kafka_notifications_topic: str = "warehouse.notifications"

    # =========================================================================
    # Redis Configuration
    # =========================================================================
    redis_host: str = "redis"
    redis_port: int = 6379
    # WH-182: Используем отдельную БД (1) для аналитики, чтобы изолировать от других данных.
    # БД 0 зарезервирована для основного приложения.
    redis_db: int = 1

    # =========================================================================
    # API Server Configuration
    # =========================================================================
    api_port: int = 8090
    api_host: str = "0.0.0.0"

    # =========================================================================
    # Aggregation Settings (WH-182: документация магических чисел)
    # =========================================================================
    # Окно агрегации метрик в секундах.
    # 60 сек - оптимальный баланс между точностью и нагрузкой на систему.
    # Увеличение снижает нагрузку, но уменьшает гранулярность данных.
    aggregation_window_seconds: int = 60

    # Максимальное количество событий в live feed.
    # 100 событий обеспечивает достаточную историю для UI без перегрузки памяти.
    # При 10 RPS это примерно 10 секунд истории.
    max_events_in_feed: int = 100

    # TTL статистики в Redis в секундах.
    # 86400 сек = 24 часа - хранение суточной статистики.
    # По истечении TTL ключи автоматически удаляются из Redis.
    stats_ttl_seconds: int = 86400

    class Config:
        env_prefix = "ANALYTICS_"
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
