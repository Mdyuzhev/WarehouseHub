"""
Analytics Service API.
WH-121: Real-time Kafka Analytics Dashboard.

FastAPI приложение с:
- REST API для получения статистики
- WebSocket для real-time обновлений
- Kafka Consumer для обработки событий
"""

import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from redis_store import store
from kafka_consumer import consumer
from websocket_manager import manager

# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Response Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    version: str
    kafka_connected: bool
    redis_connected: bool
    websocket_clients: int


class StatsResponse(BaseModel):
    total_events: int
    total_create: int
    total_update: int
    total_delete: int
    total_login: int
    total_logout: int
    total_low_stock: int
    total_out_of_stock: int
    total_notifications: int


class EventResponse(BaseModel):
    type: str
    event: str
    name: str
    timestamp: str
    user: str = None
    category: str = None
    quantity: int = None


# =============================================================================
# Lifecycle
# =============================================================================

kafka_task = None


async def on_kafka_event(event: Dict[str, Any]):
    """Callback для Kafka consumer - пересылает в WebSocket."""
    await manager.broadcast({
        "type": "event",
        "data": event
    })


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager."""
    global kafka_task

    # Startup
    logger.info("Starting Analytics Service...")

    # Подключаемся к Redis
    await store.connect()

    # Запускаем Kafka consumer
    try:
        consumer.on_event = on_kafka_event
        await consumer.start()
        kafka_task = asyncio.create_task(consumer.consume())
        logger.info("Kafka consumer started")
    except Exception as e:
        logger.warning(f"Kafka consumer failed to start: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Analytics Service...")

    if kafka_task:
        kafka_task.cancel()
        try:
            await kafka_task
        except asyncio.CancelledError:
            pass

    await consumer.stop()
    await store.close()


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Warehouse Analytics Service",
    description="Real-time analytics dashboard for warehouse operations (WH-121)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - restricted to allowed origins from config
cors_origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# =============================================================================
# HTTP Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Warehouse Analytics Service",
        "version": "1.0.0",
        "description": "Real-time Kafka analytics dashboard (WH-121)"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    kafka_ok = consumer.running if consumer else False
    redis_ok = False

    try:
        if store.redis:
            await store.redis.ping()
            redis_ok = True
    except:
        pass

    return HealthResponse(
        status="healthy" if (kafka_ok and redis_ok) else "degraded",
        version="1.0.0",
        kafka_connected=kafka_ok,
        redis_connected=redis_ok,
        websocket_clients=manager.connection_count
    )


@app.get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Возвращает общую статистику.
    """
    stats = await store.get_stats()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_events": stats.get("total_events", 0),
        "audit": {
            "create": stats.get("total_create", 0),
            "update": stats.get("total_update", 0),
            "delete": stats.get("total_delete", 0),
            "login": stats.get("total_login", 0),
            "logout": stats.get("total_logout", 0),
        },
        "notifications": {
            "total": stats.get("total_notifications", 0),
            "low_stock": stats.get("total_low_stock", 0),
            "out_of_stock": stats.get("total_out_of_stock", 0),
        }
    }


@app.get("/api/events")
async def get_events(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Возвращает последние события (live feed).
    """
    events = await store.get_events(limit=min(limit, 100))
    return events


@app.get("/api/hourly")
async def get_hourly_stats(hours: int = 24) -> List[Dict[str, Any]]:
    """
    Возвращает почасовую статистику.
    Для графика активности за последние N часов.
    """
    return await store.get_hourly_stats(hours=min(hours, 168))


@app.get("/api/daily")
async def get_daily_stats(days: int = 7) -> List[Dict[str, Any]]:
    """
    Возвращает дневную статистику.
    Для графика активности за последние N дней.
    """
    return await store.get_daily_stats(days=min(days, 30))


@app.get("/api/categories")
async def get_category_stats() -> Dict[str, Dict[str, Any]]:
    """
    Возвращает статистику по категориям товаров.
    """
    return await store.get_category_stats()


# =============================================================================
# WebSocket Endpoint
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint для real-time обновлений.

    Клиент получает:
    - Новые события в реальном времени
    - Уведомления о stock
    """
    await manager.connect(websocket)

    # Отправляем текущую статистику при подключении
    stats = await store.get_stats()
    await manager.send_personal(websocket, {
        "type": "init",
        "stats": stats,
        "clients": manager.connection_count
    })

    try:
        while True:
            # Ждём сообщения от клиента (ping/pong или команды)
            data = await websocket.receive_text()
            logger.debug(f"WebSocket received: {data}")

            # Можно обрабатывать команды от клиента
            if data == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
            elif data == "stats":
                stats = await store.get_stats()
                await manager.send_personal(websocket, {"type": "stats", "data": stats})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
