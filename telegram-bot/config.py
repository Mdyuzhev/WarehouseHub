"""
Конфигурация Telegram бота.
Все настройки в одном месте, как завещал дядюшка Боб! 🧙‍♂️
"""

import os

# =============================================================================
# Logging
# =============================================================================
# JSON format для K8s (Loki/ELK/Fluentd)
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")  # "json" или "text"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# =============================================================================
# Telegram
# =============================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITLAB_WEBHOOK_SECRET = os.getenv("GITLAB_WEBHOOK_SECRET", "")

# =============================================================================
# URLs - Staging (K8s internal DNS)
# =============================================================================
STAGING_API_URL = os.getenv(
    "STAGING_API_URL",
    "http://warehouse-api-service.warehouse.svc.cluster.local:8080"
)
STAGING_FRONTEND_URL = os.getenv(
    "STAGING_FRONTEND_URL",
    "http://warehouse-frontend-service.warehouse.svc.cluster.local"
)

# =============================================================================
# URLs - Production (Yandex Cloud)
# =============================================================================
PROD_API_URL = os.getenv("PROD_API_URL", "https://api.wh-lab.ru")
PROD_FRONTEND_URL = os.getenv("PROD_FRONTEND_URL", "https://wh-lab.ru")
PROD_HOST = os.getenv("PROD_HOST", "130.193.44.34")

# =============================================================================
# Locust (namespace loadtest)
# =============================================================================
LOCUST_MASTER_URL = os.getenv(
    "LOCUST_MASTER_URL",
    "http://locust-master.loadtest.svc.cluster.local:8089"
)

# =============================================================================
# GitLab
# =============================================================================
GITLAB_URL = os.getenv("GITLAB_URL", "http://192.168.1.74:8080")
# ⚠️ КРИТИЧНО: Токен должен быть в K8s Secret, НЕ в коде!
# Старый токен был скомпрометирован и отозван (WH-171)
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
if not GITLAB_TOKEN:
    import logging
    logging.warning("GITLAB_TOKEN not set! GitLab integrations will fail.")
GITLAB_TRIGGER_TOKEN = os.getenv("GITLAB_TRIGGER_TOKEN", "")

# Project IDs
GITLAB_PROJECTS = {
    "warehouse-master": 4,
    "warehouse-frontend": 3,
    "warehouse-api": 1,
}

# Job mappings for triggers
GITLAB_JOBS = {
    # Deploy jobs
    "deploy_api_staging": {"project": "warehouse-master", "job": "deploy-api-staging"},
    "deploy_frontend_staging": {"project": "warehouse-master", "job": "deploy-frontend-staging"},
    "deploy_all_staging": {"project": "warehouse-master", "job": "deploy-all-staging"},
    "deploy_api_prod": {"project": "warehouse-master", "job": "deploy-api-prod"},
    "deploy_frontend_prod": {"project": "warehouse-master", "job": "deploy-frontend-prod"},
    "deploy_all_prod": {"project": "warehouse-master", "job": "deploy-all-prod"},
    # E2E tests (API tests via RestAssured)
    "run_e2e_tests_staging": {"project": "warehouse-master", "job": "run-e2e-tests-staging"},
    "run_e2e_tests_prod": {"project": "warehouse-master", "job": "run-e2e-tests-prod"},
    # UI tests (Selenide)
    "run_ui_tests_staging": {"project": "warehouse-master", "job": "run-ui-tests-staging"},
    "run_ui_tests_prod": {"project": "warehouse-master", "job": "run-ui-tests-prod"},
    # Load tests
    "run_load": {"project": "warehouse-master", "job": "run-load-tests"},
}

# =============================================================================
# Allure
# =============================================================================
# Внутренний URL для API запросов (статистика)
ALLURE_SERVER_URL = os.getenv("ALLURE_SERVER_URL", "http://192.168.1.74:5050")
# Внешний URL для ссылок в сообщениях (cloudflared tunnel)
ALLURE_PUBLIC_URL = os.getenv("ALLURE_PUBLIC_URL", "https://advertiser-dark-remaining-sail.trycloudflare.com")

# =============================================================================
# Claude Proxy
# =============================================================================
CLAUDE_PROXY_URL = os.getenv("CLAUDE_PROXY_URL", "http://192.168.1.74:8765")

# =============================================================================
# Passwords (для авторизации деплоя, НТ и Claude)
# WH-172: Пароли перенесены в K8s Secret, здесь только os.getenv()
# =============================================================================
DEPLOY_PASSWORD = os.getenv("DEPLOY_PASSWORD")
LOAD_TEST_PASSWORD = os.getenv("LOAD_TEST_PASSWORD")
LOAD_TEST_GUEST_PASSWORD = os.getenv("LOAD_TEST_GUEST_PASSWORD", "Guest")  # Guest - не секрет

# Guest limits
GUEST_MAX_USERS = 20
GUEST_MAX_DURATION = 300  # 5 минут

# =============================================================================
# Prometheus (внутри K8s)
# =============================================================================
PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090"
)

# =============================================================================
# YouTrack
# WH-172: Пароль перенесён в K8s Secret
# =============================================================================
YOUTRACK_URL = os.getenv("YOUTRACK_URL", "http://192.168.1.74:8088")
YOUTRACK_USER = os.getenv("YOUTRACK_USER", "admin")
YOUTRACK_PASSWORD = os.getenv("YOUTRACK_PASSWORD")  # WH-172: в K8s Secret
YOUTRACK_PROJECT = os.getenv("YOUTRACK_PROJECT", "WH")

# =============================================================================
# Warehouse Robot
# =============================================================================
ROBOT_API_URL = os.getenv(
    "ROBOT_API_URL",
    "http://warehouse-robot-service.warehouse.svc.cluster.local:8070"
)
ROBOT_PASSWORD = os.getenv("ROBOT_PASSWORD", "1")
