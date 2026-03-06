"""
Telegram bot configuration.
Docker-compose environment.
"""

import os

# =============================================================================
# Logging
# =============================================================================
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# =============================================================================
# Telegram
# =============================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =============================================================================
# URLs - Homelab (docker-compose)
# =============================================================================
STAGING_API_URL = os.getenv("STAGING_API_URL", "http://api:8080")
STAGING_FRONTEND_URL = os.getenv("STAGING_FRONTEND_URL", "http://frontend:80")

# =============================================================================
# URLs - Production (Yandex Cloud)
# =============================================================================
PROD_API_URL = os.getenv("PROD_API_URL", "https://api.wh-lab.ru")
PROD_FRONTEND_URL = os.getenv("PROD_FRONTEND_URL", "https://wh-lab.ru")

# =============================================================================
# Health Check timeouts
# =============================================================================
HEALTH_CHECK_TIMEOUT = float(os.getenv("HEALTH_CHECK_TIMEOUT", "5.0"))
PROMETHEUS_TIMEOUT = float(os.getenv("PROMETHEUS_TIMEOUT", "3.0"))

# =============================================================================
# Prometheus (docker-compose)
# =============================================================================
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
PROMETHEUS_QUERY_WINDOW = os.getenv("PROMETHEUS_QUERY_WINDOW", "5m")

# =============================================================================
# App lifecycle
# =============================================================================
GRACEFUL_SHUTDOWN_TIMEOUT = float(os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT", "5.0"))
MAX_BACKOFF_SECONDS = int(os.getenv("MAX_BACKOFF_SECONDS", "60"))
INITIAL_BACKOFF_SECONDS = int(os.getenv("INITIAL_BACKOFF_SECONDS", "5"))

# =============================================================================
# Warehouse Robot
# =============================================================================
ROBOT_API_URL = os.getenv("ROBOT_API_URL", "")
