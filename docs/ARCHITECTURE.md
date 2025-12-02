# Warehouse Project - Architecture

> Высокоуровневая архитектура проекта. Обновлено: 2025-12-02

---

## Обзор системы

Warehouse - система управления складом, разделённая на 3 репозитория:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              РЕПОЗИТОРИИ                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ warehouse-api   │  │warehouse-frontend│  │     warehouse-master        │ │
│  │                 │  │                 │  │                             │ │
│  │ Spring Boot 3.2 │  │ Vue.js 3.4+Vite5│  │ CI/CD, K8s, Bot, Scripts   │ │
│  │ REST API        │  │ SPA             │  │ Robot, Analytics            │ │
│  │ PostgreSQL      │  │ Nginx           │  │ Orchestration               │ │
│  │ JWT + Redis     │  │                 │  │                             │ │
│  │ Kafka events    │  │                 │  │                             │ │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬──────────────┘ │
│           │                    │                          │                 │
│           └────────────────────┴──────────────────────────┘                 │
│                                │                                            │
│                    ┌───────────┴───────────┐                               │
│                    ▼                       ▼                               │
│           ┌────────────────┐      ┌────────────────┐                       │
│           │   STAGING      │      │  PRODUCTION    │                       │
│           │   K3s Cluster  │      │  Yandex Cloud  │                       │
│           │  192.168.1.74  │      │ 130.193.44.34  │                       │
│           └────────────────┘      └────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Репозитории

| Репозиторий | Путь | Назначение |
|-------------|------|------------|
| **warehouse-api** | `/home/flomaster/warehouse-api` | Backend REST API (Java 17 + Spring Boot) |
| **warehouse-frontend** | `/home/flomaster/warehouse-frontend` | Frontend SPA (Vue.js 3.4 + Vite) |
| **warehouse-master** | `/home/flomaster/warehouse-master` | Оркестрация, K8s, CI/CD, Bot |

> Детали по компонентам: [COMPONENTS.md](COMPONENTS.md)

---

## Архитектура приложения

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│                         Vue.js 3.4 + Vite 5                                 │
│                              :30081                                          │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ HTTP/REST
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WAREHOUSE API                                      │
│                      Spring Boot 3.2.0 + Java 17                            │
│                              :30080                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Controllers: AuthController, ProductController, FacilityController  │   │
│  │  Services: ProductService, AuditService, JwtService, FacilityService │   │
│  │  Security: JWT (HS256) + Facility claims, BCrypt, Rate Limiting     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────┬───────────────────────┬───────────────────────┬─────────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  PostgreSQL   │      │    Redis      │      │    Kafka      │
│    :5432      │      │    :6379      │      │    :9092      │
│  (данные)     │      │  (кэш, JWT)   │      │  (события)    │
└───────────────┘      └───────────────┘      └───────┬───────┘
                                                      │
                                  ┌───────────────────┴───────────────────┐
                                  ▼                                       ▼
                         ┌───────────────┐                       ┌───────────────┐
                         │   Analytics   │                       │    Robot      │
                         │   Service     │                       │   Service     │
                         │    :30091     │                       │    :30070     │
                         │  (WebSocket)  │                       │ (симуляция)   │
                         └───────────────┘                       └───────────────┘
```

---

## Роли пользователей

| Роль | Описание | Основные права | Facility |
|------|----------|----------------|----------|
| SUPER_USER | Суперпользователь | Полный доступ | null (глобально) |
| ADMIN | Администратор | Управление пользователями | опционально |
| MANAGER | Менеджер | Просмотр товаров и отчётов | привязан к объекту |
| EMPLOYEE | Сотрудник | CRUD товаров | привязан к объекту |
| ANALYST | Аналитик | Аналитика и дашборды | опционально |

> Детали по правам и endpoints: [TESTING.md](TESTING.md)

---

## Facilities Management (WH-269)

Иерархия логистических объектов:

```
DC (Distribution Center)
 └── WH (Warehouse)
      └── PP (Pickup Point)
```

**Коды объектов:**
- DC: `DC-001`, `DC-002`, ...
- WH: `WH-MSK-001`, `WH-SPB-002`, ...
- PP: `PP-MSK-001-01`, `PP-SPB-002-03`, ...

**JWT Claims:**
- `facilityType` - тип объекта (DC, WH, PP)
- `facilityId` - ID объекта
- `facilityCode` - код объекта

> Backward compatibility: JWT без facility claims поддерживаются

---

## Окружения

### Staging (K3s)

```
Host: 192.168.1.74

K8s Namespaces:
├── warehouse        # API, Frontend, PostgreSQL, Redis, Kafka, Robot, Analytics
├── warehouse-dev    # Dev окружение (31xxx порты)
├── loadtest         # Locust
├── notifications    # Telegram Bot
└── monitoring       # Prometheus, Grafana
```

### Production (Yandex Cloud)

```
Host: 130.193.44.34

Docker Compose:
├── api        → https://api.wh-lab.ru
├── frontend   → https://wh-lab.ru
├── postgres
├── redis
├── kafka
└── nginx + certbot
```

> Детали по инфраструктуре: [INFRASTRUCTURE_GUIDE.md](INFRASTRUCTURE_GUIDE.md)

---

## CI/CD Pipeline

### Dual Environment (WH-200)

| Ветка | Окружение | Namespace | Порты | Деплой |
|-------|-----------|-----------|-------|--------|
| `develop` | Development | warehouse-dev | 31xxx | **Auto** |
| `main` | Production | warehouse | 30xxx | **Manual** |

```
develop → push → build → test → deploy-dev (auto) → warehouse-dev
                                     ↓
                              merge request
                                     ↓
main    → push → build → test → deploy-prod (manual) → warehouse
```

> Детали по CI/CD: [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)

---

## Мониторинг

| Инструмент | URL | Назначение |
|------------|-----|------------|
| Grafana | http://192.168.1.74:30300 | Визуализация метрик |
| Prometheus | http://192.168.1.74:30090 | Сбор метрик |
| Locust | http://192.168.1.74:30089 | Нагрузочное тестирование |
| Allure | http://192.168.1.74:5252 | Отчёты по тестам |

> Детали по тестированию: [TESTING.md](TESTING.md), [LOAD_TESTING.md](LOAD_TESTING.md)

---

## Связанная документация

| Документ | Описание |
|----------|----------|
| [COMPONENTS.md](COMPONENTS.md) | Детали компонентов, порты, технологии |
| [INFRASTRUCTURE_GUIDE.md](INFRASTRUCTURE_GUIDE.md) | K8s namespaces, сервисы, порты |
| [TESTING.md](TESTING.md) | API тестирование, учётки, endpoints |
| [LOAD_TESTING.md](LOAD_TESTING.md) | k6, Locust, очистка данных |
| [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) | Процедуры деплоя |
| [CREDENTIALS.md](CREDENTIALS.md) | Секреты и пароли |
| [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) | Решение проблем |
| [YOUTRACK_API.md](YOUTRACK_API.md) | YouTrack API |

---

*Последнее обновление: 2025-12-02*
