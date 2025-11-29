"""
🎮 Конфиг для Warehouse Orchestrator UI
Все секреты здесь (ну, почти все)
"""

import os
from pathlib import Path

# Пути
BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR.parent / "scripts"
DATA_DIR = BASE_DIR / "data"

# Создаём папку для данных если нет
DATA_DIR.mkdir(exist_ok=True)

# SQLite для истории чата
SQLITE_DB = DATA_DIR / "agent_history.db"

# Claude API (через прокси)
CLAUDE_PROXY_URL = os.getenv("CLAUDE_PROXY_URL", "http://192.168.1.74:8765")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# GitLab API
GITLAB_URL = os.getenv("GITLAB_URL", "http://192.168.1.74:8080")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "glpat-Ou0qfvnfGfUOGkbs3nmv8m86MQp1OjEH.01.0w0ojabq3")

# GitLab проекты и джобы
GITLAB_PROJECTS = {
    "warehouse-master": {"id": 4, "name": "warehouse-master"},
    "warehouse-api": {"id": 1, "name": "warehouse-api"},
    "warehouse-frontend": {"id": 2, "name": "warehouse-frontend"},
}

# Джобы которые можно запускать (project_id -> jobs)
GITLAB_JOBS = {
    4: [  # warehouse-master
        {"name": "deploy-api-staging", "display": "🔧 API → Staging", "stage": "deploy-staging"},
        {"name": "deploy-frontend-staging", "display": "🎨 Frontend → Staging", "stage": "deploy-staging"},
        {"name": "deploy-all-staging", "display": "🚀 ALL → Staging", "stage": "deploy-staging"},
        {"name": "deploy-api-prod", "display": "🔧 API → Prod", "stage": "deploy-prod", "danger": True},
        {"name": "deploy-frontend-prod", "display": "🎨 Frontend → Prod", "stage": "deploy-prod", "danger": True},
        {"name": "deploy-all-prod", "display": "🚀 ALL → Prod", "stage": "deploy-prod", "danger": True},
        {"name": "run-e2e-tests", "display": "🧪 E2E Tests", "stage": "test"},
        {"name": "run-load-tests", "display": "📊 Load Tests", "stage": "test"},
        {"name": "deploy-telegram-bot", "display": "🤖 Bot", "stage": "deploy-staging"},
        {"name": "deploy-orchestrator-ui", "display": "🎮 UI", "stage": "deploy-staging"},
    ]
}

# Kubernetes
KUBECONFIG = os.getenv("KUBECONFIG", os.path.expanduser("~/.kube/config"))

# Сервисы (для мониторинга) — только те что реально есть
SERVICES = {
    "api": {
        "name": "warehouse-api",
        "namespace": "warehouse",
        "icon": "🔧",
        "url": "http://192.168.1.74:30080",
        "health_endpoint": "/actuator/health"
    },
    "frontend": {
        "name": "warehouse-frontend",
        "namespace": "warehouse",
        "icon": "🎨",
        "url": "http://192.168.1.74:30081",
        "health_endpoint": "/"
    },
    "postgres": {
        "name": "postgres",
        "namespace": "warehouse",
        "icon": "🗄️",
        "url": None,
        "health_endpoint": None
    }
}

# Забавные сообщения для разных ситуаций
MESSAGES = {
    "deploy_start": [
        "🚀 Поехали! Деплоим как в последний раз...",
        "🎮 LEVEL UP! Запускаю деплой...",
        "🔥 Жмём на газ! Деплой в процессе...",
    ],
    "deploy_success": [
        "✨ Задеплоилось! Чудеса случаются!",
        "🎉 GG WP! Деплой прошёл успешно!",
        "🏆 VICTORY! Всё в проде!",
    ],
    "deploy_fail": [
        "💀 GAME OVER! Деплой упал...",
        "🔥 Хьюстон, у нас проблемы!",
        "☠️ Ну, бывает... Откатываемся?",
    ],
    "tests_start": [
        "🧪 Запускаю тесты, держи кулачки...",
        "🎰 Крутим барабан тестов!",
    ],
    "tests_success": [
        "✅ Все тесты зелёные! Как так-то?!",
        "🎯 100% ACCURACY! Тесты прошли!",
    ],
    "tests_fail": [
        "❌ Тесты красные, но это фича, не баг!",
        "🐛 Нашли баги! Это хорошо... наверное.",
    ],
}
