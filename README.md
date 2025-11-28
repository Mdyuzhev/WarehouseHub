# Warehouse Master

Мастер-репозиторий для оркестрации деплоя, тестирования и управления инфраструктурой проекта Warehouse.

## Структура

```
warehouse-master/
├── .gitlab-ci.yml           # Главный пайплайн оркестрации
├── k8s/                     # Kubernetes манифесты
│   ├── warehouse/           # API + Frontend
│   ├── loadtest/            # Locust (нагрузочное тестирование)
│   ├── notifications/       # Telegram Bot
│   └── monitoring/          # Prometheus
├── loadtest/                # Скрипты нагрузочного тестирования
│   └── locustfile.py        # Сценарии Locust
├── e2e-tests/               # E2E тесты (RestAssured + Allure)
│   └── src/test/java/...    # Java тесты
├── telegram-bot/            # Исходники Telegram бота
│   ├── app.py               # Основной код бота
│   ├── claude_proxy.py      # Прокси для Claude API
│   └── Dockerfile
├── docs/                    # Документация
│   ├── ARCHITECTURE.md      # Архитектура репозиториев
│   └── TROUBLESHOOTING_GUIDE.md  # Руководство по устранению проблем
└── .claude/                 # Контекст для Claude AI
    ├── project-context.md
    └── settings.local.json
```

## Доступные CI/CD действия

| Действие | Описание | Триггер |
|----------|----------|---------|
| `deploy-api-staging` | Деплой API в K8s | Manual |
| `deploy-frontend-staging` | Деплой Frontend в K8s | Manual |
| `deploy-all-staging` | Деплой API + Frontend | Manual |
| `deploy-api-prod` | Деплой API на Yandex Cloud | Manual |
| `deploy-frontend-prod` | Деплой Frontend на Yandex Cloud | Manual |
| `deploy-all-prod` | Деплой всего на prod | Manual |
| `run-e2e-tests` | Запуск E2E тестов + Allure отчёт | Manual |
| `run-load-tests` | Нагрузочное тестирование Locust | Manual |
| `deploy-telegram-bot` | Деплой Telegram бота в K8s | Manual |

## Связанные репозитории

- **warehouse-api** - Spring Boot REST API (только бизнес-логика)
- **warehouse-frontend** - Vue.js SPA (только UI код)

## Инфраструктура

| Среда | URL | Описание |
|-------|-----|----------|
| Staging API | http://192.168.1.74:30080 | K3s кластер |
| Staging Frontend | http://192.168.1.74:30081 | K3s кластер |
| Production API | https://api.wh-lab.ru | Yandex Cloud |
| Production Frontend | https://wh-lab.ru | Yandex Cloud |
| Locust UI | http://192.168.1.74:30089 | Нагрузочное тестирование |
| Prometheus | http://192.168.1.74:30090 | Мониторинг |
| Allure | http://192.168.1.74:5252 | Отчёты E2E тестов |
| GitLab | http://192.168.1.74:8080 | CI/CD |
| YouTrack | http://192.168.1.74:8088 | Трекер задач |

## Быстрый старт

### Деплой в Staging
```bash
# Через GitLab CI - запустить pipeline вручную
# Или через kubectl:
kubectl apply -f k8s/warehouse/
kubectl rollout restart deployment/warehouse-api -n warehouse
```

### Запуск E2E тестов
```bash
# Из корня warehouse-api:
./mvnw test -Dtest="*E2ETest" -Dspring.profiles.active=test
```

### Запуск нагрузочных тестов
```bash
# Локально:
locust -f loadtest/locustfile.py --host=http://192.168.1.74:30080

# В K8s:
kubectl apply -f k8s/loadtest/
```
