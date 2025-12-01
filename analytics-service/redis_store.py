"""
Redis Store for Analytics.
WH-121: Хранение агрегированных метрик в Redis.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import redis.asyncio as redis

from config import settings

logger = logging.getLogger(__name__)


class RedisStore:
    """Хранилище аналитики в Redis."""

    # Ключи Redis
    EVENTS_LIST = "analytics:events"  # Последние события (list)
    STATS_HASH = "analytics:stats"  # Общая статистика (hash)
    HOURLY_KEY = "analytics:hourly:{date}:{hour}"  # Почасовая статистика
    DAILY_KEY = "analytics:daily:{date}"  # Дневная статистика
    CATEGORY_KEY = "analytics:category:{category}"  # По категориям

    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Подключение к Redis."""
        self.redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        try:
            await self.redis.ping()
            logger.info(f"Connected to Redis: {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise

    async def close(self):
        """Закрытие соединения."""
        if self.redis:
            await self.redis.close()

    async def add_event(self, event: Dict[str, Any]):
        """
        Добавляет событие в live feed.
        Хранит последние N событий.
        """
        event_json = json.dumps(event, default=str)

        # Добавляем в начало списка
        await self.redis.lpush(self.EVENTS_LIST, event_json)

        # Обрезаем до max_events
        await self.redis.ltrim(self.EVENTS_LIST, 0, settings.max_events_in_feed - 1)

    async def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Возвращает последние события из live feed."""
        events = await self.redis.lrange(self.EVENTS_LIST, 0, limit - 1)
        return [json.loads(e) for e in events]

    async def increment_stat(self, stat_name: str, amount: int = 1):
        """Увеличивает счётчик статистики."""
        await self.redis.hincrby(self.STATS_HASH, stat_name, amount)

    async def set_stat(self, stat_name: str, value: Any):
        """Устанавливает значение статистики."""
        await self.redis.hset(self.STATS_HASH, stat_name, str(value))

    async def get_stats(self) -> Dict[str, Any]:
        """Возвращает всю статистику."""
        stats = await self.redis.hgetall(self.STATS_HASH)
        # Преобразуем числовые значения
        result = {}
        for k, v in stats.items():
            try:
                result[k] = int(v)
            except ValueError:
                try:
                    result[k] = float(v)
                except ValueError:
                    result[k] = v
        return result

    async def record_hourly_event(self, event_type: str):
        """
        Записывает событие в почасовую статистику.
        Используется для графиков активности.
        """
        now = datetime.utcnow()
        key = self.HOURLY_KEY.format(date=now.strftime("%Y-%m-%d"), hour=now.hour)

        await self.redis.hincrby(key, event_type, 1)
        await self.redis.hincrby(key, "total", 1)

        # TTL 48 часов
        await self.redis.expire(key, 48 * 3600)

    async def record_daily_event(self, event_type: str):
        """Записывает событие в дневную статистику."""
        now = datetime.utcnow()
        key = self.DAILY_KEY.format(date=now.strftime("%Y-%m-%d"))

        await self.redis.hincrby(key, event_type, 1)
        await self.redis.hincrby(key, "total", 1)

        # TTL 30 дней
        await self.redis.expire(key, 30 * 86400)

    async def record_category_event(self, category: str, event_type: str, value: float = 0):
        """Записывает событие по категории."""
        key = self.CATEGORY_KEY.format(category=category or "unknown")

        await self.redis.hincrby(key, f"{event_type}_count", 1)
        if value:
            await self.redis.hincrbyfloat(key, f"{event_type}_value", value)

        await self.redis.expire(key, settings.stats_ttl_seconds)

    async def get_hourly_stats(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Возвращает почасовую статистику за последние N часов."""
        now = datetime.utcnow()
        result = []

        for i in range(hours):
            dt = now - timedelta(hours=i)
            key = self.HOURLY_KEY.format(date=dt.strftime("%Y-%m-%d"), hour=dt.hour)

            stats = await self.redis.hgetall(key)
            result.append({
                "hour": dt.strftime("%Y-%m-%d %H:00"),
                "stats": {k: int(v) for k, v in stats.items()} if stats else {}
            })

        return list(reversed(result))

    async def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Возвращает дневную статистику за последние N дней."""
        now = datetime.utcnow()
        result = []

        for i in range(days):
            dt = now - timedelta(days=i)
            key = self.DAILY_KEY.format(date=dt.strftime("%Y-%m-%d"))

            stats = await self.redis.hgetall(key)
            result.append({
                "date": dt.strftime("%Y-%m-%d"),
                "stats": {k: int(v) for k, v in stats.items()} if stats else {}
            })

        return list(reversed(result))

    async def get_category_stats(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает статистику по категориям."""
        # Находим все ключи категорий
        keys = []
        async for key in self.redis.scan_iter(match="analytics:category:*"):
            keys.append(key)

        result = {}
        for key in keys:
            category = key.split(":")[-1]
            stats = await self.redis.hgetall(key)
            result[category] = {}
            for k, v in stats.items():
                try:
                    result[category][k] = float(v) if "." in v else int(v)
                except ValueError:
                    result[category][k] = v

        return result


# Глобальный экземпляр
store = RedisStore()
