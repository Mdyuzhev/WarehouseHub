# WarehouseHub

**Warehouse Management System** - полнофункциональная система управления складом с микросервисной архитектурой, развёрнутая в Kubernetes.

## Обзор

Проект представляет собой комплексное решение для автоматизации складских операций, включающее:

- REST API на Spring Boot
- SPA-интерфейс на Vue.js
- Автоматизированное тестирование (E2E, нагрузочное, UI)
- CI/CD пайплайны
- Мониторинг и алертинг
- Telegram-бот для уведомлений

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        Production                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Frontend   │───▶│   API       │───▶│ PostgreSQL  │         │
│  │  (Vue.js)   │    │(Spring Boot)│    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                            │                                     │
│                            ▼                                     │
│                     ┌─────────────┐                             │
│                     │    Redis    │                             │
│                     │   (Cache)   │                             │
│                     └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

## Структура репозитория

```
warehouse-master/
├── k8s/                      # Kubernetes манифесты
│   ├── warehouse/            # Production namespace
│   ├── warehouse-dev/        # Development namespace
│   ├── loadtest/             # Нагрузочное тестирование
│   ├── monitoring/           # Prometheus + Grafana
│   └── notifications/        # Telegram Bot
│
├── e2e-tests/                # E2E тесты (RestAssured + Allure)
│   └── src/test/java/        # Java тесты
│
├── PerformanceTesting/       # Нагрузочное тестирование
│   ├── configs/              # Конфигурации k6
│   └── scripts/              # Скрипты тестов
│
├── ui-tests/                 # UI тесты (Selenoid)
│
├── telegram-bot/             # Telegram бот для уведомлений
│   ├── app.py                # Основной код
│   └── Dockerfile
│
├── docs/                     # Документация
│   ├── ARCHITECTURE.md
│   ├── COMPONENTS.md
│   ├── DEPLOY_GUIDE.md
│   ├── TESTING.md
│   └── TROUBLESHOOTING_GUIDE.md
│
├── .gitlab-ci.yml            # CI/CD пайплайн
└── .claude/                  # AI-агент контекст
```

## Технологический стек

### Backend
- Java 17
- Spring Boot 3.x
- Spring Security + JWT
- Spring Data JPA
- PostgreSQL 15
- Redis (кэширование)

### Frontend
- Vue.js 3
- Vite
- Pinia (state management)
- Axios

### Infrastructure
- Kubernetes (K3s)
- Docker
- GitLab CI/CD
- Nginx Ingress

### Testing
- JUnit 5 + RestAssured (E2E)
- k6 (нагрузочное)
- Locust (нагрузочное)
- Selenoid (UI)
- Allure (отчёты)

### Monitoring
- Prometheus
- Grafana
- Loki (логи)

## Функциональность

### Управление товарами
- CRUD операции
- Категоризация
- Поиск и фильтрация
- Массовый импорт/экспорт

### Складские операции
- Приёмка товаров
- Отгрузка
- Инвентаризация
- Перемещение между зонами

### Аналитика
- Остатки в реальном времени
- История движения
- Отчёты по периодам

### Пользователи и роли
- SUPER_USER - полный доступ
- ADMIN - управление пользователями
- MANAGER - складские операции
- EMPLOYEE - базовые операции

## Быстрый старт

### Требования
- Docker & Docker Compose
- Kubernetes cluster (опционально)
- Java 17+ (для разработки)
- Node.js 18+ (для фронтенда)

### Локальный запуск

```bash
# Клонировать репозиторий
git clone https://github.com/Mdyuzhev/WaregouseHub.git
cd WaregouseHub

# Запуск через Docker Compose
docker-compose up -d

# Или деплой в Kubernetes
kubectl apply -f k8s/warehouse/
```

### Переменные окружения

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=warehouse
DB_USER=warehouse
DB_PASSWORD=***

# JWT
JWT_SECRET=***

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

## CI/CD

Проект использует GitLab CI/CD с ручными триггерами:

| Job | Описание |
|-----|----------|
| `deploy-api-staging` | Деплой API в staging |
| `deploy-frontend-staging` | Деплой Frontend в staging |
| `deploy-all-prod` | Деплой в production |
| `run-e2e-tests` | E2E тесты + Allure отчёт |
| `run-load-tests` | Нагрузочное тестирование |

## Тестирование

### E2E тесты
```bash
cd e2e-tests
./mvnw test -Dtest="*E2ETest"
```

### Нагрузочные тесты (k6)
```bash
k6 run PerformanceTesting/scripts/load-test.js
```

### UI тесты
```bash
cd ui-tests
./mvnw test
```

## Документация

- [Архитектура](docs/ARCHITECTURE.md)
- [Компоненты](docs/COMPONENTS.md)
- [Руководство по деплою](docs/DEPLOY_GUIDE.md)
- [Тестирование](docs/TESTING.md)
- [Troubleshooting](docs/TROUBLESHOOTING_GUIDE.md)

## Связанные репозитории

| Репозиторий | Описание |
|-------------|----------|
| warehouse-api | Spring Boot REST API |
| warehouse-frontend | Vue.js SPA |

## Лицензия

Private repository. All rights reserved.

---

**Maintainer:** [@Mdyuzhev](https://github.com/Mdyuzhev)
