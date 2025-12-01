# Warehouse Project - Architecture

> Полная архитектура проекта. Обновлено: 2025-12-02 (WH-200 CI/CD Dual Environment)

---

## Оглавление

1. [Обзор системы](#обзор-системы)
2. [Репозитории](#репозитории)
3. [warehouse-api](#warehouse-api)
4. [warehouse-frontend](#warehouse-frontend)
5. [warehouse-master](#warehouse-master)
6. [Новые компоненты (WH-120, WH-121)](#новые-компоненты-wh-120-wh-121)
7. [Инфраструктура Staging](#инфраструктура-staging)
8. [Инфраструктура Production](#инфраструктура-production)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Мониторинг и тестирование](#мониторинг-и-тестирование)
11. [QA подсистема (WH-155)](#qa-подсистема-wh-155)
12. [Сетевая схема](#сетевая-схема)
13. [Dev-окружение (WH-192)](#dev-окружение-wh-192)
14. [Dual Environment CI/CD (WH-200)](#dual-environment-cicd-wh-200)

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

| Репозиторий | Путь | GitLab ID | Назначение |
|-------------|------|-----------|------------|
| **warehouse-api** | `/home/flomaster/warehouse-api` | 1 | Backend REST API |
| **warehouse-frontend** | `/home/flomaster/warehouse-frontend` | 3 | Frontend SPA |
| **warehouse-master** | `/home/flomaster/warehouse-master` | 4 | Оркестрация, инфраструктура |

---

## warehouse-api

**Технологии:** Java 17, Spring Boot 3.2.0, PostgreSQL, JWT 0.11.5, Kafka, Redis

### Структура
```
warehouse-api/
├── src/main/java/com/warehouse/
│   ├── config/
│   │   ├── SecurityConfig.java      # Spring Security + JWT
│   │   ├── MetricsConfig.java       # Prometheus метрики
│   │   ├── KafkaConfig.java         # Kafka producer + topics
│   │   ├── RedisConfig.java         # Redis кэширование
│   │   ├── GlobalExceptionHandler.java
│   │   └── DataInitializer.java     # Начальные пользователи
│   ├── model/
│   │   ├── User.java                # Сущность пользователя (implements UserDetails)
│   │   ├── Product.java             # Сущность товара
│   │   └── Role.java                # Enum ролей (5 ролей)
│   ├── repository/
│   │   ├── UserRepository.java
│   │   └── ProductRepository.java
│   ├── service/
│   │   ├── ProductService.java      # CRUD + Kafka events
│   │   ├── AuditService.java        # Логирование в Kafka
│   │   ├── StockNotificationService.java  # Алерты о низких остатках
│   │   ├── RateLimitingService.java # Rate limiting (Redis)
│   │   ├── TokenBlacklistService.java # JWT blacklist (Redis)
│   │   ├── AuthTokenCacheService.java # Кэш JWT токенов
│   │   └── CustomUserDetailsService.java
│   ├── security/
│   │   ├── JwtService.java          # HS256, генерация/валидация JWT
│   │   └── JwtAuthenticationFilter.java
│   ├── controller/
│   │   ├── AuthController.java      # /api/auth/*
│   │   └── ProductController.java   # /api/products/*
│   ├── dto/
│   │   ├── AuthRequest.java
│   │   ├── AuthResponse.java
│   │   ├── RegisterRequest.java
│   │   ├── AuditEvent.java
│   │   └── StockNotification.java
│   └── WarehouseApiApplication.java
├── src/main/resources/
│   ├── application.properties       # Локальный конфиг
│   └── application-k8s.properties   # Конфиг для K8s (Redis, Kafka)
├── src/test/
│   ├── java/.../controller/ProductControllerTest.java
│   └── resources/application-test.properties  # H2 для тестов
├── Dockerfile                       # Multi-stage build (temurin:17-alpine)
├── pom.xml                          # Maven зависимости
└── .gitlab-ci.yml                   # CI pipeline
```

### Роли пользователей (Role.java)

| Роль | Описание | Права |
|------|----------|-------|
| **SUPER_USER** | Суперпользователь | Полный доступ ко всему |
| **ADMIN** | Администратор | Управление пользователями, статус системы |
| **MANAGER** | Менеджер | Просмотр отчётов и товаров (read-only) |
| **EMPLOYEE** | Сотрудник | Работа с товарами (CRUD) |
| **ANALYST** | Аналитик (WH-121) | Доступ к аналитике и дашбордам |

### Зависимости (pom.xml)

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| Spring Boot | 3.2.0 | Framework |
| jjwt-* | 0.11.5 | JWT создание/валидация (HS256) |
| springdoc-openapi | 2.3.0 | Swagger UI |
| rest-assured | 5.4.0 | Тестирование |
| allure-* | 2.25.0 | Отчёты |
| micrometer-prometheus | - | Метрики |
| spring-kafka | - | Kafka producer |
| spring-data-redis | - | Кэширование |

### API Endpoints

| Метод | Endpoint | Описание | Роли |
|-------|----------|----------|------|
| POST | `/api/auth/login` | Авторизация | public |
| POST | `/api/auth/register` | Регистрация | public |
| GET | `/api/auth/me` | Текущий пользователь | authenticated |
| POST | `/api/auth/logout` | Выход (blacklist token) | authenticated |
| GET | `/api/products` | Список товаров | authenticated |
| GET | `/api/products?category=X` | Фильтр по категории | authenticated |
| POST | `/api/products` | Создать товар | SUPER_USER, EMPLOYEE |
| PUT | `/api/products/{id}` | Обновить товар | SUPER_USER, EMPLOYEE |
| DELETE | `/api/products/{id}` | Удалить товар | SUPER_USER, EMPLOYEE |
| GET | `/actuator/health` | Health check | public |
| GET | `/actuator/prometheus` | Метрики | public |
| GET | `/swagger-ui.html` | Swagger UI | public |

### Kafka Topics

| Topic | Описание | События |
|-------|----------|---------|
| `warehouse.audit` | События аудита | CREATE, UPDATE, DELETE, LOGIN, LOGOUT |
| `warehouse.notifications` | Уведомления склада | LOW_STOCK, OUT_OF_STOCK |

### Redis Ключи

| Pattern | TTL | Назначение |
|---------|-----|------------|
| `rate_limit:login:*` | 15 мин | Rate limiting (5 попыток) |
| `jwt_blacklist:*` | до exp токена | Blacklisted tokens |
| `auth:token:*` | 1 час | Кэш JWT токенов |
| `products` | 5 мин | Кэш списка товаров |
| `productsByCategory:*` | 5 мин | Кэш по категориям |

### JWT Конфигурация

| Параметр | Значение |
|----------|----------|
| Алгоритм | HS256 |
| Expiration | 24 часа (86400000 ms) |
| Claims | subject, role, iat, exp |

---

## warehouse-frontend

**Технологии:** Vue.js 3.4, Vite 5, Vue Router 4

### Структура
```
warehouse-frontend/
├── src/
│   ├── components/
│   │   ├── LoginPage.vue       # Страница входа (443 строки)
│   │   ├── HomePage.vue        # Главная - список товаров (530 строк)
│   │   ├── AddProductPage.vue  # Добавление товара (237 строк)
│   │   ├── StatusPage.vue      # Статус системы (534 строки)
│   │   └── AnalyticsPage.vue   # Real-time аналитика (903 строки)
│   ├── services/
│   │   └── auth.js             # Аутентификация + API + permissions (186 строк)
│   ├── utils/
│   │   └── apiConfig.js        # Определение API URL (54 строки)
│   ├── router/
│   │   └── index.js            # Vue Router (98 строк)
│   ├── App.vue                 # Навигация + роли (227 строк)
│   └── main.js
├── src/__tests__/              # Vitest тесты
│   ├── App.test.js
│   └── auth.test.js            # 140+ assertions
├── public/
├── index.html                  # Runtime API URL скрипт
├── nginx.conf                  # Nginx конфиг для SPA
├── Dockerfile                  # Multi-stage (node:20 → nginx:alpine)
├── vite.config.js              # minify:false, treeshake:false
├── package.json
└── .env.production             # VITE_API_URL для прода
```

### Роуты (router/index.js)

| Путь | Компонент | Требуемые роли |
|------|-----------|----------------|
| `/login` | LoginPage | - |
| `/` | HomePage | authenticated |
| `/add` | AddProductPage | edit-products permission |
| `/status` | StatusPage | SUPER_USER, ADMIN |
| `/analytics` | AnalyticsPage | SUPER_USER, ADMIN, MANAGER, ANALYST |

### Permissions (auth.js)

| Permission | Роли |
|------------|------|
| `system-status` | SUPER_USER, ADMIN |
| `user-management` | SUPER_USER, ADMIN |
| `view-products` | SUPER_USER, ADMIN, MANAGER, EMPLOYEE |
| `edit-products` | SUPER_USER, EMPLOYEE |
| `view-reports` | SUPER_USER, ADMIN, MANAGER |
| `view-analytics` | SUPER_USER, ADMIN, MANAGER, ANALYST |

### Важно: API URL определение

Vite агрессивно оптимизирует код при сборке. Для правильной работы на разных окружениях:

1. **index.html** - runtime скрипт ДО загрузки бандла:
```html
<script>
  (function() {
    var host = window.location.hostname;
    if (host === 'wh-lab.ru' || host === 'www.wh-lab.ru') {
      window.__API_URL__ = 'https://api.wh-lab.ru/api';
      window.__ANALYTICS_URL__ = 'https://analytics.wh-lab.ru';
    } else if (host === '192.168.1.74') {
      window.__API_URL__ = 'http://192.168.1.74:30080/api';
      window.__ANALYTICS_URL__ = 'http://192.168.1.74:30091';
    } else {
      window.__API_URL__ = 'http://' + host + ':30080/api';
      window.__ANALYTICS_URL__ = 'http://' + host + ':30091';
    }
  })();
</script>
```

2. **auth.js** - использует `new Function()` для обхода оптимизации Vite
3. **vite.config.js** - `minify: false`, `treeshake: false` для сохранения runtime логики

### Зависимости (package.json)

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| vue | ^3.4.0 | Framework |
| vue-router | ^4.0.0 | Routing |
| vite | ^5.0.0 | Bundler |
| vitest | ^1.2.0 | Testing |

---

## warehouse-master

**Назначение:** Оркестрация деплоя, K8s манифесты, CI/CD, инструменты

### Структура
```
warehouse-master/
├── .claude/
│   └── settings.local.json     # Настройки Claude Code + audit
├── docs/
│   ├── ARCHITECTURE.md         # ← Этот файл
│   ├── INFRASTRUCTURE_GUIDE.md # Полная инвентаризация
│   ├── TROUBLESHOOTING_GUIDE.md
│   ├── DEPLOY_GUIDE.md         # Процедуры деплоя
│   ├── CREDENTIALS.md          # Все секреты
│   ├── YOUTRACK_API.md
│   └── RELEASE_NOTES_WH-120-121.md
├── k8s/
│   ├── warehouse/              # API + Frontend + PostgreSQL + доп. сервисы
│   │   ├── api-deployment.yaml        # 2 replicas
│   │   ├── api-service.yaml           # NodePort 30080
│   │   ├── api-configmap.yaml
│   │   ├── api-secret.yaml
│   │   ├── api-servicemonitor.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── frontend-service.yaml      # NodePort 30081
│   │   ├── frontend-ingress.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── redis-service.yaml
│   │   ├── redis-configmap.yaml
│   │   ├── kafka-deployment.yaml      # Kafka KRaft (без Zookeeper)
│   │   ├── kafka-service.yaml
│   │   ├── kafka-configmap.yaml
│   │   └── selenoid*.yaml             # Selenoid в K8s
│   ├── robot/                  # Warehouse Robot (WH-120)
│   │   ├── kustomization.yaml
│   │   ├── robot-deployment.yaml
│   │   ├── robot-service.yaml         # NodePort 30070
│   │   └── robot-secrets.yaml
│   ├── analytics/              # Analytics Service (WH-121)
│   │   ├── kustomization.yaml
│   │   ├── analytics-deployment.yaml
│   │   └── analytics-service.yaml     # NodePort 30091
│   ├── loadtest/               # Locust нагрузочное тестирование
│   │   ├── namespace.yaml
│   │   ├── locust-configmap.yaml
│   │   ├── locust-deployment.yaml     # master + 5 workers
│   │   └── locust-service.yaml        # NodePort 30089
│   ├── notifications/          # Telegram Bot
│   │   ├── bot-deployment.yaml
│   │   ├── bot-service.yaml           # NodePort 30088
│   │   └── bot-secret.yaml
│   └── monitoring/             # Prometheus + Grafana
│       ├── namespace.yaml
│       ├── prometheus-*.yaml          # NodePort 30090
│       ├── grafana-*.yaml             # NodePort 30300
│       └── alertmanager-*.yaml
├── warehouse-robot/            # Robot Service (WH-120)
│   ├── api.py                  # FastAPI приложение
│   ├── robot.py                # CLI интерфейс
│   ├── api_client.py           # HTTP клиент для Warehouse API
│   ├── config.py               # Конфигурация
│   ├── scenarios/              # Сценарии работы
│   │   ├── base.py
│   │   ├── receiving.py        # Приёмка товара
│   │   ├── shipping.py         # Отгрузка
│   │   └── inventory.py        # Инвентаризация
│   ├── Dockerfile              # Python 3.11-slim
│   └── requirements.txt        # FastAPI, httpx, faker, schedule
├── analytics-service/          # Analytics Service (WH-121)
│   ├── app.py                  # FastAPI + WebSocket + Kafka
│   ├── config.py               # Конфигурация
│   ├── kafka_consumer.py       # Kafka consumer
│   ├── redis_store.py          # Redis хранилище статистики
│   ├── websocket_manager.py    # WebSocket менеджер
│   ├── Dockerfile              # Python 3.11-slim
│   └── requirements.txt        # FastAPI, aiokafka, aioredis
├── telegram-bot/               # Telegram бот v5.4
│   ├── app.py                  # Точка входа (26.5 KB)
│   ├── config.py               # Все настройки
│   ├── bot/
│   │   ├── handlers/
│   │   │   ├── commands.py     # /start, /status, /help, /release
│   │   │   ├── deploy.py       # Деплой команды
│   │   │   ├── testing.py      # Тесты и НТ (QA меню)
│   │   │   ├── claude.py       # AI интеграция
│   │   │   ├── pm.py           # PM Dashboard (YouTrack)
│   │   │   ├── robot.py        # Robot control (WH-120)
│   │   │   └── gitlab_webhook.py
│   │   ├── keyboards.py
│   │   ├── messages.py
│   │   └── telegram.py
│   ├── services/
│   │   ├── gitlab.py
│   │   ├── locust.py
│   │   ├── allure.py
│   │   ├── health.py
│   │   ├── youtrack.py         # YouTrack API
│   │   └── robot.py            # Robot API client
│   ├── claude_proxy.py         # Прокси для Anthropic API
│   └── Dockerfile              # Python 3.11-slim
├── orchestrator-ui/            # 8-bit консоль управления
│   ├── app/
│   │   ├── main.py             # FastAPI приложение
│   │   ├── agent.py            # Claude AI агент
│   │   ├── gitlab.py           # GitLab API
│   │   ├── services.py         # K8s статусы
│   │   ├── database.py         # SQLite история
│   │   └── config.py           # Конфигурация
│   ├── templates/              # Jinja2 шаблоны
│   ├── static/                 # CSS, JS
│   └── docker-compose.yml      # network_mode: host
├── loadtest/
│   └── locustfile.py           # Сценарий нагрузки (17 KB)
├── scripts/
│   ├── deploy-local.sh         # Локальный деплой в K3s
│   └── load-test.sh            # Запуск НТ
├── selenoid/                   # Selenoid (Docker Compose)
│   ├── docker-compose.yml
│   └── config/browsers.json    # Chrome 127/128, Firefox 125
├── e2e-tests/                  # API E2E тесты (RestAssured)
│   ├── pom.xml                 # Java 17, RestAssured 5.4.0, Allure 2.25.0
│   ├── mvnw
│   └── src/test/java/com/warehouse/e2e/
│       ├── base/BaseE2ETest.java
│       ├── config/TestConfig.java
│       └── tests/
│           ├── HealthApiTest.java
│           ├── AuthApiTest.java
│           └── ProductsApiTest.java
├── ui-tests/                   # UI тесты (Selenide + Allure)
│   ├── pom.xml                 # Selenide 7.0.4
│   ├── mvnw
│   └── src/test/java/com/warehouse/ui/
│       ├── config/
│       │   ├── TestConfig.java
│       │   └── BaseTest.java
│       ├── pages/
│       │   ├── LoginPage.java
│       │   ├── ProductsPage.java
│       │   └── AnalyticsPage.java
│       └── tests/
│           ├── LoginTest.java
│           ├── AnalyticsTest.java
│           └── RoleAccessTest.java
└── .gitlab-ci.yml              # Главный пайплайн
```

---

## Новые компоненты (WH-120, WH-121)

### Warehouse Robot (WH-120)

**Описание:** Симулятор складских операций для тестирования и демонстрации

**Технологии:** Python 3.11, FastAPI 0.109.0, httpx, faker, schedule

**Порт:** 30070

#### API Endpoints
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Информация о сервисе |
| GET | `/health` | Health check |
| GET | `/status` | Текущий статус робота |
| GET | `/stats` | Статистика выполнения |
| GET | `/scenarios` | Список сценариев |
| POST | `/start` | Запуск сценария |
| POST | `/stop` | Остановка робота |
| POST | `/schedule` | Запланировать запуск |
| GET | `/scheduled` | Список запланированных |
| DELETE | `/scheduled/{id}` | Отменить запланированный |

#### Сценарии
| Сценарий | Описание |
|----------|----------|
| `receiving` | Приёмка товара — создание 3-7 новых позиций |
| `shipping` | Отгрузка — уменьшение остатков 2-5 товаров |
| `inventory` | Инвентаризация — корректировка ±5 единиц |

#### Скорости
| Скорость | Задержка между действиями |
|----------|---------------------------|
| `slow` | 3-5 секунд |
| `normal` | 1-3 секунды |
| `fast` | 0.3-1 секунда |

### Analytics Service (WH-121)

**Описание:** Real-time Kafka аналитика с WebSocket

**Технологии:** Python 3.11, FastAPI 0.109.0, aiokafka 0.10.0, aioredis, WebSocket

**Порт:** 30091

#### API Endpoints
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/health` | Health check (Kafka + Redis статус) |
| GET | `/api/stats` | Агрегированная статистика |
| GET | `/api/events` | Последние события (limit до 100) |
| GET | `/api/hourly` | Почасовая статистика (до 168 часов) |
| GET | `/api/daily` | Дневная статистика (до 30 дней) |
| GET | `/api/categories` | Статистика по категориям |
| WS | `/ws` | Real-time события |

#### WebSocket сообщения
| Тип | Описание |
|-----|----------|
| `init` | Начальная статистика при подключении |
| `stats` | Обновление статистики |
| `event` | Новое событие |
| `pong` | Ответ на ping |

### Telegram Bot (v5.4)

**Handlers:**
- `commands` — /start, /help, /status, /health, /metrics, /pods, /release
- `deploy` — Деплой staging/production
- `testing` — E2E тесты, UI тесты, Load testing
- `claude` — AI интеграция
- `pm` — PM Dashboard (YouTrack)
- `robot` — Robot control + schedule (WH-120)
- `gitlab_webhook` — GitLab webhooks

**Services:**
- `gitlab` — GitLab API
- `health` — Health checks
- `locust` — Load testing
- `allure` — Test reports
- `youtrack` — Issue tracker
- `robot` — Robot API client

---

## Инфраструктура Staging

**Host:** `192.168.1.74` (K3s + Docker)

### K8s Namespaces

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           K3s CLUSTER                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  namespace: warehouse                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐    │   │
│  │  │ postgres-0   │  │ warehouse-api    │  │ warehouse-frontend │    │   │
│  │  │ StatefulSet  │  │ Deployment (2)   │  │ Deployment (1)     │    │   │
│  │  │ :5432        │  │ :8080 → :30080   │  │ :80 → :30081       │    │   │
│  │  └──────────────┘  └──────────────────┘  └────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐    │   │
│  │  │ redis        │  │ kafka (KRaft)    │  │ postgres-replica-0 │    │   │
│  │  │ Deployment   │  │ Deployment       │  │ StatefulSet        │    │   │
│  │  │ :6379        │  │ :9092            │  │ :5432 (read only)  │    │   │
│  │  └──────────────┘  └──────────────────┘  └────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐    │   │
│  │  │ warehouse-   │  │ analytics-       │  │ selenoid           │    │   │
│  │  │ robot        │  │ service          │  │ Deployment         │    │   │
│  │  │ :8070→:30070 │  │ :8090→:30091     │  │ :4444→:30040       │    │   │
│  │  └──────────────┘  └──────────────────┘  └────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  namespace: loadtest                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌──────────────┐  ┌───────────────┐  ┌────────────────────────┐   │   │
│  │  │ locust-master│  │ locust-worker │  │ locust-exporter        │   │   │
│  │  │ Deployment   │  │ Deployment (5)│  │ (Prometheus metrics)   │   │   │
│  │  │ :8089→:30089 │  │               │  │                        │   │   │
│  │  └──────────────┘  └───────────────┘  └────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  namespace: notifications                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────┐                                │   │
│  │  │ gitlab-telegram-bot (v5.4)      │                                │   │
│  │  │ Deployment (1)                  │                                │   │
│  │  │ :8000 → :30088 (webhook)        │                                │   │
│  │  └─────────────────────────────────┘                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  namespace: monitoring                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌──────────────┐  ┌────────────────┐  ┌────────────────────────┐  │   │
│  │  │ prometheus   │  │ grafana        │  │ alertmanager           │  │   │
│  │  │ Deployment   │  │ Deployment     │  │ StatefulSet            │  │   │
│  │  │ :9090→:30090 │  │ :3000 → :30300 │  │ :9093                  │  │   │
│  │  └──────────────┘  └────────────────┘  └────────────────────────┘  │   │
│  │  ┌──────────────────┐  ┌─────────────────────────┐                 │   │
│  │  │ kube-state-metrics│  │ prometheus-node-exporter│                 │   │
│  │  └──────────────────┘  └─────────────────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  namespace: warehouse-dev (WH-192)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐    │   │
│  │  │ postgres     │  │ warehouse-api    │  │ warehouse-frontend │    │   │
│  │  │ Deployment   │  │ Deployment (1)   │  │ Deployment (1)     │    │   │
│  │  │ :5432→:31432 │  │ :8080 → :31080   │  │ :80 → :31081       │    │   │
│  │  └──────────────┘  └──────────────────┘  └────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌──────────────┐                                                   │   │
│  │  │ redis        │  ResourceQuota: 4 CPU, 8Gi Memory                │   │
│  │  │ Deployment   │  Изолировано от prod (warehouse namespace)       │   │
│  │  │ :6379→:31379 │                                                   │   │
│  │  └──────────────┘                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Docker Compose сервисы (на хосте)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DOCKER COMPOSE (HOST)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ gitlab (gitlab/gitlab-ce:latest)                                      │  │
│  │ Ports: 8080 (HTTP), 8443 (HTTPS), 2222 (SSH)                         │  │
│  │ URL: http://192.168.1.74:8080                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ youtrack (jetbrains/youtrack:2024.3)                                  │  │
│  │ Ports: 8088                                                           │  │
│  │ URL: http://192.168.1.74:8088                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ allure-server + allure-ui                                             │  │
│  │ Ports: 5050 (API), 5252 (UI)                                         │  │
│  │ URL: http://192.168.1.74:5252                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ warehouse-orchestrator-ui                                             │  │
│  │ Ports: 8000 (network_mode: host)                                      │  │
│  │ URL: http://192.168.1.74:8000                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ selenoid + selenoid-ui (Docker, не K8s)                               │  │
│  │ Ports: 4444 (Selenium Hub), 8090 (UI)                                │  │
│  │ URL: http://192.168.1.74:4444/wd/hub                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### NodePorts Summary (Staging - Production Environment)

| Service | NodePort | Internal | URL |
|---------|----------|----------|-----|
| warehouse-api | 30080 | 8080 | http://192.168.1.74:30080 |
| warehouse-frontend | 30081 | 80 | http://192.168.1.74:30081 |
| warehouse-robot | 30070 | 8070 | http://192.168.1.74:30070 |
| analytics-service | 30091 | 8090 | http://192.168.1.74:30091 |
| selenoid (K8s) | 30040 | 4444 | http://192.168.1.74:30040 |
| postgres-external | 30432 | 5432 | - |
| locust-master | 30089 | 8089 | http://192.168.1.74:30089 |
| telegram-bot-webhook | 30088 | 8000 | http://192.168.1.74:30088 |
| prometheus | 30090 | 9090 | http://192.168.1.74:30090 |
| grafana | 30300 | 3000 | http://192.168.1.74:30300 |

### NodePorts Summary (Staging - Development Environment, WH-192)

| Service | NodePort | Internal | URL |
|---------|----------|----------|-----|
| warehouse-api (dev) | 31080 | 8080 | http://192.168.1.74:31080 |
| warehouse-frontend (dev) | 31081 | 80 | http://192.168.1.74:31081 |
| postgres-external (dev) | 31432 | 5432 | - |
| redis-external (dev) | 31379 | 6379 | - |

### Docker Compose сервисы (на хосте)

| Service | Port | URL |
|---------|------|-----|
| GitLab | 8080 | http://192.168.1.74:8080 |
| YouTrack | 8088 | http://192.168.1.74:8088 |
| Allure Server | 5050 | http://192.168.1.74:5050 |
| Allure UI | 5252 | http://192.168.1.74:5252 |
| Orchestrator UI | 8000 | http://192.168.1.74:8000 |
| Claude Proxy | 8765 | http://192.168.1.74:8765 |
| Selenoid (Docker) | 4444 | http://192.168.1.74:4444/wd/hub |
| Selenoid UI | 8090 | http://192.168.1.74:8090 |

---

## Инфраструктура Production

**Host:** `130.193.44.34` (Yandex Cloud VM)
**User:** `ubuntu`
**Путь:** `/opt/warehouse`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PRODUCTION (Yandex Cloud)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Docker Compose                                   │  │
│  │                                                                       │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ warehouse-api  │  │warehouse-frontend│  │ postgres             │  │  │
│  │  │ :8080          │  │ :80              │  │ :5432                │  │  │
│  │  └───────┬────────┘  └───────┬──────────┘  └──────────────────────┘  │  │
│  │          │                   │                                       │  │
│  │          └─────────┬─────────┘                                       │  │
│  │                    ▼                                                 │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │                    Nginx Reverse Proxy                        │   │  │
│  │  │                    + Let's Encrypt SSL                        │   │  │
│  │  │                                                               │   │  │
│  │  │   api.wh-lab.ru  ──────────────────────► :8080 (API)         │   │  │
│  │  │   wh-lab.ru      ──────────────────────► :80   (Frontend)    │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Public URLs:                                                               │
│  • https://wh-lab.ru        - Frontend                                     │
│  • https://api.wh-lab.ru    - API                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Container Registry

```
Yandex Container Registry: cr.yandex/crpf5fukf1ili7kudopb
├── warehouse-api:latest
├── warehouse-api:{commit-sha}
├── warehouse-frontend:latest
└── warehouse-frontend:{commit-sha}
```

---

## CI/CD Pipeline

### Dual Environment Workflow (WH-200)

С декабря 2025 настроен dual environment CI/CD:

| Ветка | Окружение | Namespace | Порты | Деплой |
|-------|-----------|-----------|-------|--------|
| `develop` | Development | `warehouse-dev` | 31xxx | **Автоматический** |
| `main` | Production | `warehouse` | 30xxx | **Ручной (manual)** |

### warehouse-api Pipeline
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  validate → build → test → package → deploy                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  validate:     mvnw validate                                                │
│  build:        mvnw compile                                                 │
│  test:         mvnw test (unit tests, H2 DB, exclude E2E)                  │
│  package:      mvnw package -DskipTests                                     │
│                docker build --no-cache                                      │
│                docker push → Yandex Registry                                │
│                docker save → k3s ctr images import                          │
│                                                                             │
│  deploy-dev:   (develop branch, AUTO)                                       │
│                kubectl rollout restart -n warehouse-dev                     │
│                Health check: http://192.168.1.74:31080/actuator/health      │
│                                                                             │
│  deploy-prod:  (main branch, MANUAL)                                        │
│                kubectl rollout restart -n warehouse                         │
│                Health check: http://192.168.1.74:30080/actuator/health      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### warehouse-frontend Pipeline
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  test → build → package → deploy                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  test:         npm ci && npm test                                          │
│  build:        npm run build                                                │
│  package:      docker build (multi-stage: node → nginx)                     │
│                docker push → Yandex Registry                                │
│                docker save → k3s ctr images import                          │
│                                                                             │
│  deploy-dev:   (develop branch, AUTO)                                       │
│                kubectl rollout restart -n warehouse-dev                     │
│                Availability check: http://192.168.1.74:31081/               │
│                                                                             │
│  deploy-prod:  (main branch, MANUAL)                                        │
│                kubectl rollout restart -n warehouse                         │
│                Availability check: http://192.168.1.74:30081/               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### warehouse-master Pipeline (Manual Triggers)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  deploy-staging │ deploy-prod │ test                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STAGING (kubectl apply + rollout restart):                                 │
│  • deploy-api-staging                                                       │
│  • deploy-frontend-staging                                                  │
│  • deploy-all-staging                                                       │
│  • deploy-telegram-bot                                                      │
│  • deploy-orchestrator-ui                                                   │
│  • deploy-robot                                                             │
│  • deploy-analytics                                                         │
│                                                                             │
│  PRODUCTION (SSH + docker compose):                                         │
│  • deploy-api-prod                                                          │
│  • deploy-frontend-prod                                                     │
│  • deploy-all-prod                                                          │
│                                                                             │
│  TESTING:                                                                   │
│  • run-e2e-tests-staging (mvnw test + Allure upload)                       │
│  • run-e2e-tests-prod                                                       │
│  • run-ui-tests-staging (Selenide + Allure)                                │
│  • run-ui-tests-prod                                                        │
│  • run-load-tests (Locust API)                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Мониторинг и тестирование

### Prometheus + Grafana
- **Prometheus:** http://192.168.1.74:30090 - сбор метрик
- **Grafana:** http://192.168.1.74:30300 - визуализация
  - **Дашборд "Warehouse API"** - метрики приложения:
    - Request Rate (req/sec)
    - Response Time (avg/max latency)
    - Error Rate (4xx/5xx)
    - JVM Memory (heap used/max)
    - Database Connections (HikariCP)
    - Business Metrics (products created/deleted)
    - Service Health (UP/DOWN)
- **Alertmanager:** алертинг
- **Node Exporter:** метрики хоста
- **Kube State Metrics:** метрики K8s

### Allure Report Server
- **API (internal):** http://192.168.1.74:5050
- **UI (internal):** http://192.168.1.74:5252
- **Public URL (cloudflared):** https://advertiser-dark-remaining-sail.trycloudflare.com
- **Projects (WH-155):**
  - `e2e-staging` — E2E тесты на staging
  - `e2e-prod` — E2E тесты на production
  - `ui-staging` — UI тесты на staging
  - `ui-prod` — UI тесты на production

### Locust Load Testing
- **UI:** http://192.168.1.74:30089
- **Workers:** 5 replicas (оптимизировано после НТ)
- **Target:** warehouse-api-service.warehouse.svc.cluster.local:8080
- **Результаты НТ (WH-103):**
  - Max Users (0% ошибок): **150**
  - Max RPS: **63**
  - Max Users (<2% ошибок): **350-400**
- **Сценарии:**
  - EmployeeUser (weight 70%): создание товаров
  - ManagerUser (weight 30%): просмотр

### Analytics Dashboard (WH-121)
- **URL:** http://192.168.1.74:30091
- **Frontend:** http://192.168.1.74:30081/analytics
- **Features:**
  - Real-time WebSocket события
  - Статистика по типам операций
  - Почасовые/дневные графики
  - Алерты склада (Low Stock, Out of Stock)

---

## QA подсистема (WH-155)

### Архитектура QA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Telegram Bot QA Menu                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🔬 QA (главное меню)                                                       │
│      │                                                                      │
│      ├── 🧪 STAGING                                                         │
│      │   ├── 📝 E2E → run-e2e-tests-staging → Allure (e2e-staging)         │
│      │   ├── 🎭 UI  → run-ui-tests-staging  → Allure (ui-staging)          │
│      │   └── 🔥 Нагрузочное → Locust UI                                    │
│      │                                                                      │
│      └── 🚀 PRODUCTION                                                      │
│          ├── 📝 E2E → run-e2e-tests-prod → Allure (e2e-prod)               │
│          ├── 🎭 UI  → run-ui-tests-prod  → Allure (ui-prod)                │
│          └── 🔥 Нагрузочное → Locust UI                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Allure Projects (4 проекта)

| Project ID | Описание | GitLab Job | URL |
|------------|----------|------------|-----|
| `e2e-staging` | E2E API тесты на staging | `run-e2e-tests-staging` | http://192.168.1.74:5050/.../e2e-staging |
| `e2e-prod` | E2E API тесты на prod | `run-e2e-tests-prod` | http://192.168.1.74:5050/.../e2e-prod |
| `ui-staging` | UI тесты на staging | `run-ui-tests-staging` | http://192.168.1.74:5050/.../ui-staging |
| `ui-prod` | UI тесты на prod | `run-ui-tests-prod` | http://192.168.1.74:5050/.../ui-prod |

### Selenoid

**Docker Compose (хост):**
- **Selenium Hub:** http://192.168.1.74:4444/wd/hub
- **Selenoid UI:** http://192.168.1.74:8090

**K8s (warehouse namespace):**
- **Selenium Hub:** http://192.168.1.74:30040

**Браузеры:** Chrome 127/128, Firefox 125

### E2E тесты (e2e-tests/)

**Технологии:** Java 17, RestAssured 5.4.0, JUnit 5, Allure 2.25.0

| Тестовый класс | Описание |
|----------------|----------|
| `AuthApiTest` | Авторизация, роли, негативные сценарии |
| `ProductsApiTest` | CRUD товаров, права доступа, валидация |
| `HealthApiTest` | Health check эндпоинты |

### UI тесты (ui-tests/)

**Технологии:** Java 17, Selenide 7.0.4, JUnit 5, Allure 2.25.0

| Тестовый класс | Описание |
|----------------|----------|
| `LoginTest` | Авторизация пользователей |
| `AnalyticsTest` | Доступ analyst/admin к /analytics |
| `RoleAccessTest` | Проверка ролей |

---

## Сетевая схема

```
                                    INTERNET
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                    ▼                                       ▼
            ┌───────────────┐                      ┌───────────────┐
            │  wh-lab.ru    │                      │ api.wh-lab.ru │
            │  (Frontend)   │                      │   (API)       │
            └───────┬───────┘                      └───────┬───────┘
                    │                                      │
                    └──────────────┬───────────────────────┘
                                   │
                                   ▼
                          ┌───────────────────┐
                          │   NGINX + SSL     │
                          │  130.193.44.34    │
                          │    (PROD)         │
                          └───────────────────┘


            ┌──────────────────────────────────────────────┐
            │              LOCAL NETWORK                    │
            │                                              │
            │   ┌────────────────────────────────────┐    │
            │   │        192.168.1.74 (STAGING)       │    │
            │   │                                     │    │
            │   │  K8s NodePorts:                    │    │
            │   │  :30080  → API                     │    │
            │   │  :30081  → Frontend                │    │
            │   │  :30070  → Robot                   │    │
            │   │  :30091  → Analytics               │    │
            │   │  :30089  → Locust                  │    │
            │   │  :30090  → Prometheus              │    │
            │   │  :30300  → Grafana                 │    │
            │   │  :30088  → Telegram Bot Webhook    │    │
            │   │  :30040  → Selenoid (K8s)          │    │
            │   │  :30432  → PostgreSQL              │    │
            │   │                                     │    │
            │   │  Docker (host):                    │    │
            │   │  :8080   → GitLab                  │    │
            │   │  :8088   → YouTrack                │    │
            │   │  :5050   → Allure API              │    │
            │   │  :5252   → Allure UI               │    │
            │   │  :8000   → Orchestrator UI         │    │
            │   │  :8765   → Claude Proxy            │    │
            │   │  :4444   → Selenoid Hub (Docker)   │    │
            │   │  :8090   → Selenoid UI             │    │
            │   │                                     │    │
            │   └────────────────────────────────────┘    │
            │                                              │
            └──────────────────────────────────────────────┘
```

---

## Тестовые пользователи

> Пароль для всех: `password123`

| Username | Full Name | Role | Права |
|----------|-----------|------|-------|
| `superuser` | Суперпользователь | SUPER_USER | Все |
| `admin` | Администратор | ADMIN | Управление пользователями |
| `manager` | Менеджер склада | MANAGER | Просмотр товаров |
| `employee` | Сотрудник склада | EMPLOYEE | Создание товаров |
| `analyst` | Аналитик | ANALYST | Только аналитика (WH-121) |
| `ivanov` | Иванов Алексей Петрович | SUPER_USER | Все |
| `petrova` | Петрова Мария Сергеевна | ADMIN | Управление пользователями |
| `sidorov` | Сидоров Дмитрий Андреевич | MANAGER | Просмотр товаров |
| `kozlova` | Козлова Анна Викторовна | EMPLOYEE | Создание товаров |

---

## Актуальный статус подов (2025-12-02)

### Production Environment (warehouse namespace)

| Namespace | Pod | Replicas | Status |
|-----------|-----|----------|--------|
| warehouse | warehouse-api | 2 | Running |
| warehouse | warehouse-frontend | 1 | Running |
| warehouse | warehouse-robot | 1 | Running |
| warehouse | analytics-service | 1 | Running |
| warehouse | postgres-0 | 1 | Running |
| warehouse | postgres-replica-0 | 1 | Running |
| warehouse | redis | 1 | Running |
| warehouse | kafka | 1 | Running |
| warehouse | selenoid | 1 | Running |

### Development Environment (warehouse-dev namespace, WH-192)

| Namespace | Pod | Replicas | Status |
|-----------|-----|----------|--------|
| warehouse-dev | warehouse-api | 1 | Running |
| warehouse-dev | warehouse-frontend | 1 | Running |
| warehouse-dev | postgres | 1 | Running |
| warehouse-dev | redis | 1 | Running |

### Service Namespaces

| Namespace | Pod | Replicas | Status |
|-----------|-----|----------|--------|
| loadtest | locust-master | 1 | Running |
| loadtest | locust-worker | 5 | Running |
| loadtest | locust-exporter | 1 | Running |
| notifications | gitlab-telegram-bot | 1 | Running |
| monitoring | prometheus | 1 | Running |
| monitoring | grafana | 2 | Running |
| monitoring | alertmanager | 1 | Running |

---

## WH-170: Улучшения и стабилизация (15 задач)

### Выполненные задачи

| ID | Название | Статус |
|----|----------|--------|
| WH-171 | Расширенный мониторинг UI тестов | ✅ Fixed |
| WH-172 | Унификация тестовых окружений | ✅ Fixed |
| WH-173 | Расширенный мониторинг E2E тестов | ✅ Fixed |
| WH-174 | Параметризация конфигов Robot | ✅ Fixed |
| WH-175 | Расширенный мониторинг Locust | ✅ Fixed |
| WH-176 | Параметризация конфигов Analytics | ✅ Fixed |
| WH-177 | Параметризация конфигов Telegram Bot | ✅ Fixed |
| WH-178 | Интеграция метрик Robot | ✅ Fixed |
| WH-179 | Конфигурируемые таймауты Robot | ✅ Fixed |
| WH-180 | Конфигурируемые таймауты Analytics | ✅ Fixed |
| WH-181 | Конфигурируемые таймауты Telegram Bot | ✅ Fixed |
| WH-182 | Документация magic numbers | ✅ Fixed |
| WH-183 | .env.example для всех сервисов | ✅ Fixed |
| WH-184 | Защита секретов в .gitignore | ✅ Fixed |
| WH-185 | Унификация Locust файлов | ✅ Fixed |

### Ключевые улучшения WH-170

**Конфигурация через .env:**
- `telegram-bot/.env.example` - все настройки бота
- `warehouse-robot/.env.example` - конфигурация робота
- `analytics-service/.env.example` - Kafka, Redis, агрегация

**Защита секретов (.gitignore):**
- `.env`, `*.env.local` - игнорируются
- `credentials.json`, `secrets.yaml` - игнорируются
- `*.pem`, `*.key`, `*.crt` - игнорируются
- `!.env.example` - шаблоны разрешены

**Унифицированный Locust (loadtest/locustfile.py):**
- 4 типа пользователей: SuperUser (10%), AdminUser (20%), ManagerUser (30%), EmployeeUser (50%)
- JWT кэширование с thread-safe lock
- 2 профиля: LinearLoadShape, StepLoadShape

---

## Dev-окружение (WH-192)

### Назначение

Dev-окружение создано для параллельной разработки и тестирования новых фич без влияния на production (warehouse namespace).

### Компоненты

| Компонент | Namespace | Port | Описание |
|-----------|-----------|------|----------|
| warehouse-api | warehouse-dev | 31080 | API для разработки |
| warehouse-frontend | warehouse-dev | 31081 | Frontend для разработки |
| postgres | warehouse-dev | 31432 | Отдельная БД |
| redis | warehouse-dev | 31379 | Отдельный кэш |

### Особенности

- **ResourceQuota:** 4 CPU, 8Gi Memory (ограничение ресурсов)
- **Изоляция:** Полная изоляция от prod (warehouse namespace)
- **Данные:** Отдельные PostgreSQL и Redis экземпляры
- **Секреты:** Собственные secrets (warehouse-dev-secret)

### Git Flow (WH-187)

```
main (protected) ─────────────────────────────────────────────► production
    │                                                              │
    └── develop ─────► feature/* ─────► MR ─────► develop ────────┘
                                                      │
                                                      ▼
                                              warehouse-dev (auto deploy)
```

---

## Dual Environment CI/CD (WH-200)

### Workflow

| Действие | Ветка | Pipeline | Деплой |
|----------|-------|----------|--------|
| Push в develop | develop | Запускается | AUTO в warehouse-dev |
| Push в main | main | Запускается | MANUAL в warehouse |
| Merge Request | develop → main | После approve | MANUAL trigger |

### GitLab Environments

| Environment | URL API | URL Frontend | Описание |
|-------------|---------|--------------|----------|
| development | http://192.168.1.74:31080 | http://192.168.1.74:31081 | Для develop branch |
| production | http://192.168.1.74:30080 | http://192.168.1.74:30081 | Для main branch |

### Проверенные Pipelines

| Pipeline | Branch | Status | Результат |
|----------|--------|--------|-----------|
| #208 (warehouse-api) | develop | SUCCESS | Auto deploy в dev |
| #209 (warehouse-frontend) | develop | SUCCESS | Auto deploy в dev |
| #210 (warehouse-api) | main | MANUAL | Ожидает ручного запуска |
| #211 (warehouse-frontend) | main | MANUAL | Ожидает ручного запуска |

---

## WH-186 Logistics Hub Epic

### Структура эпика

```
WH-186 (Epic: Logistics Hub) [Fixed]
├── WH-187 (User Story: Настройка GitLab для параллельной разработки) [Fixed]
│     ├── WH-188 (Task: Создать ветку develop от main) [Fixed]
│     ├── WH-189 (Task: Настроить protected branch rules для main) [Fixed]
│     ├── WH-190 (Task: Создать шаблон merge request) [Fixed]
│     └── WH-191 (Task: Документировать git flow в README) [Fixed]
│
├── WH-192 (User Story: Создание dev-окружения в K8s) [Fixed]
│     ├── WH-193 (Task: Создать namespace warehouse-dev с labels) [Fixed]
│     ├── WH-194 (Task: Применить ResourceQuota для ограничения ресурсов) [Fixed]
│     ├── WH-195 (Task: Развернуть PostgreSQL на порту 31432) [Fixed]
│     ├── WH-196 (Task: Развернуть Redis на порту 31379) [Fixed]
│     ├── WH-197 (Task: Скопировать deployments API и frontend с новыми портами) [Fixed]
│     ├── WH-198 (Task: Создать secrets для dev-окружения) [Fixed]
│     └── WH-199 (Task: Проверить изоляцию от prod) [Fixed]
│
└── WH-200 (User Story: CI/CD pipeline для dual environment) [Fixed]
      ├── WH-201 (Task: Добавить стадию deploy-dev в .gitlab-ci.yml) [Fixed]
      ├── WH-202 (Task: Модифицировать deploy-prod с manual trigger) [Fixed]
      ├── WH-203 (Task: Настроить GitLab Environments) [Fixed]
      ├── WH-204 (Task: Добавить переменные окружения для dev) [Fixed]
      └── WH-205 (Task: Протестировать pipeline на обеих ветках) [Fixed]
```

---

*Последнее обновление: 2025-12-02 (WH-200 CI/CD Dual Environment - Logistics Hub Epic)*
