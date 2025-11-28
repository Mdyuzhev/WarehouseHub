# 🎯 Warehouse Master

Мастер-репозиторий для оркестрации деплоя, тестирования и управления инфраструктурой проекта Warehouse.

## 📁 Структура

```
warehouse-master/
├── .gitlab-ci.yml           # Главный пайплайн оркестрации
├── pipelines/               # Модульные пайплайны
│   ├── deploy-api.yml       # Деплой API
│   ├── deploy-frontend.yml  # Деплой Frontend
│   ├── deploy-all.yml       # Деплой всего
│   ├── e2e-tests.yml        # E2E тестирование
│   └── load-tests.yml       # Нагрузочное тестирование
├── scripts/                 # Скрипты деплоя
├── k8s/                     # Kubernetes манифесты
│   ├── warehouse/           # API + Frontend + DB
│   ├── loadtest/            # Locust
│   ├── notifications/       # Telegram Bot
│   └── monitoring/          # Prometheus + Grafana
├── telegram-bot/            # Исходники бота
└── .claude/                 # Контекст для Claude AI
```

## 🚀 Доступные действия

| Действие | Описание | Триггер |
|----------|----------|---------|
| Deploy API Staging | Деплой API в K8s | Manual |
| Deploy Frontend Staging | Деплой Frontend в K8s | Manual |
| Deploy All Staging | Деплой API + Frontend | Manual |
| Deploy Production | Деплой в Yandex Cloud | Manual |
| Run E2E Tests | Запуск E2E тестов | Manual |
| Run Load Tests | Нагрузочное тестирование | Manual |

## 🔗 Связанные репозитории

- **warehouse-api** - Spring Boot REST API
- **warehouse-frontend** - Vue.js SPA

## 📊 Инфраструктура

- **Staging:** K3s кластер (192.168.1.74)
- **Production:** Yandex Cloud (130.193.44.34)
- **Мониторинг:** Prometheus + Grafana
- **CI/CD:** GitLab CI
