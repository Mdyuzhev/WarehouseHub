"""
Warehouse Uplink Bot v1.0
Sends notifications to Uplink (Matrix) via botservice webhook.
No polling — notification-only service.
"""

import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from config import LOG_FORMAT, LOG_LEVEL, UPLINK_WEBHOOK_URL
from bot import uplink
from bot.messages import format_robot_notification, format_health_message
from services import check_all_health


# =============================================================================
# Logging
# =============================================================================
def setup_logging():
    import json
    import sys

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "service": "uplink-bot",
                "version": "1.0.0"
            }
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_obj, ensure_ascii=False)

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    if LOG_FORMAT.lower() == "json":
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logging.root.handlers = [handler]
        logging.root.setLevel(level)
    else:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger(__name__)


# =============================================================================
# FastAPI App
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    if UPLINK_WEBHOOK_URL:
        logger.info(f"Uplink bot started, webhook: {UPLINK_WEBHOOK_URL}")
    else:
        logger.warning("UPLINK_WEBHOOK_URL not set — notifications will be skipped")
    yield
    logger.info("Uplink bot stopped")


app = FastAPI(
    title="Warehouse Uplink Bot",
    description="Notifications to Uplink (Matrix) via webhook",
    version="1.0.0",
    lifespan=lifespan
)


# =============================================================================
# HTTP Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "uplink_configured": bool(UPLINK_WEBHOOK_URL),
    }


@app.get("/")
async def root():
    return {
        "name": "Warehouse Uplink Bot",
        "version": "1.0.0",
    }


# =============================================================================
# Robot Notifications
# =============================================================================

class RobotNotification(BaseModel):
    scenario: str
    result: Dict[str, Any]


@app.post("/robot/notify")
async def robot_notify(notification: RobotNotification):
    try:
        logger.info(f"Received robot notification: scenario={notification.scenario}")
        plain, html = format_robot_notification(notification.scenario, notification.result)
        success = await uplink.send_message(text=plain, html=html)
        return {"status": "ok", "sent": success}
    except Exception as e:
        logger.error(f"Robot notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Deploy Notifications
# =============================================================================

class DeployNotification(BaseModel):
    status: str
    commit_message: str = ""
    commit_hash: str = ""
    commit_author: str = ""
    elapsed: float = None
    error: str = None


@app.post("/deploy/notify")
async def deploy_notify(notification: DeployNotification):
    try:
        logger.info(f"Received deploy notification: status={notification.status}")
        success = await uplink.send_deploy_event(
            status=notification.status,
            commit_message=notification.commit_message,
            commit_hash=notification.commit_hash,
            commit_author=notification.commit_author,
            elapsed=notification.elapsed,
            error=notification.error,
        )
        return {"status": "ok", "sent": success}
    except Exception as e:
        logger.error(f"Deploy notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Health Status Notification
# =============================================================================

@app.post("/health/notify")
async def health_notify():
    """Check infrastructure health and send report to Uplink."""
    try:
        health_data = await check_all_health()
        plain, html = format_health_message(health_data)
        success = await uplink.send_message(text=plain, html=html)
        return {"status": "ok", "sent": success}
    except Exception as e:
        logger.error(f"Health notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Generic Message
# =============================================================================

class MessagePayload(BaseModel):
    text: str
    html: str = None


@app.post("/send")
async def send_generic(payload: MessagePayload):
    """Send arbitrary message to Uplink."""
    try:
        success = await uplink.send_message(text=payload.text, html=payload.html)
        return {"status": "ok", "sent": success}
    except Exception as e:
        logger.error(f"Send message error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
