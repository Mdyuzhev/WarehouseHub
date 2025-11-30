# Warehouse Project - Architecture

> Полная архитектура проекта. Обновлено: 2025-11-30 (НТ завершено)

---

## Оглавление

1. [Обзор системы](#обзор-системы)
2. [Репозитории](#репозитории)
3. [warehouse-api](#warehouse-api)
4. [warehouse-frontend](#warehouse-frontend)
5. [warehouse-master](#warehouse-master)
6. [Инфраструктура Staging](#инфраструктура-staging)
7. [Инфраструктура Production](#инфраструктура-production)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Мониторинг и тестирование](#мониторинг-и-тестирование)
10. [UI и E2E тестирование](#ui-и-e2e-тестирование)
11. [Сетевая схема](#сетевая-схема)

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
│  │ Spring Boot     │  │ Vue.js 3 + Vite │  │ CI/CD, K8s, Bot, Scripts   │ │
│  │ REST API        │  │ SPA             │  │ Orchestration               │ │
│  │ PostgreSQL      │  │ Nginx           │  │                             │ │
│  │ JWT Auth        │  │                 │  │                             │ │
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

**Технологии:** Java 17, Spring Boot 3.2, PostgreSQL, JWT

### Структура
```
warehouse-api/
├── src/main/java/com/warehouse/
│   ├── config/
│   │   ├── SecurityConfig.java      # Spring Security + JWT
│   │   ├── MetricsConfig.java       # Prometheus метрики
│   │   ├── GlobalExceptionHandler.java
│   │   └── DataInitializer.java     # Начальные пользователи
│   ├── model/
│   │   ├── User.java                # Сущность пользователя
│   │   ├── Product.java             # Сущность товара
│   │   └── Role.java                # Enum ролей (SUPER_USER, ADMIN, MANAGER, EMPLOYEE)
│   ├── repository/
│   │   ├── UserRepository.java
│   │   └── ProductRepository.java
│   ├── service/
│   │   ├── ProductService.java
│   │   └── CustomUserDetailsService.java
│   ├── security/
│   │   ├── JwtService.java          # Генерация/валидация JWT
│   │   └── JwtAuthenticationFilter.java
│   ├── controller/
│   │   ├── AuthController.java      # /api/auth/login, /api/auth/me
│   │   └── ProductController.java   # CRUD /api/products
│   ├── dto/
│   │   ├── AuthRequest.java
│   │   ├── AuthResponse.java
│   │   └── RegisterRequest.java
│   └── WarehouseApiApplication.java
├── src/main/resources/
│   ├── application.properties       # Основной конфиг
│   └── application-k8s.properties   # Конфиг для K8s
├── src/test/
│   ├── java/.../controller/ProductControllerTest.java
│   └── resources/application-test.properties  # H2 для тестов
├── Dockerfile                       # Multi-stage build
├── pom.xml                          # Maven зависимости
└── .gitlab-ci.yml                   # CI pipeline
```

### Зависимости (pom.xml)
- Spring Boot Starters: web, data-jpa, security, actuator, validation
- JWT: jjwt-api, jjwt-impl, jjwt-jackson (0.11.5)
- Database: PostgreSQL (runtime), H2 (test)
- Docs: springdoc-openapi (Swagger UI)
- Metrics: micrometer-registry-prometheus
- Testing: RestAssured, Allure, AssertJ, Awaitility

### API Endpoints
| Метод | Endpoint | Описание | Роли |
|-------|----------|----------|------|
| POST | `/api/auth/login` | Авторизация | public |
| GET | `/api/auth/me` | Текущий пользователь | authenticated |
| GET | `/api/products` | Список товаров | authenticated |
| POST | `/api/products` | Создать товар | EMPLOYEE+ |
| PUT | `/api/products/{id}` | Обновить товар | EMPLOYEE+ |
| DELETE | `/api/products/{id}` | Удалить товар | MANAGER+ |
| GET | `/actuator/health` | Health check | public |
| GET | `/actuator/prometheus` | Метрики | public |
| GET | `/swagger-ui.html` | Swagger UI | public |

---

## warehouse-frontend

**Технологии:** Vue.js 3.4, Vite 5, Vue Router 4

### Структура
```
warehouse-frontend/
├── src/
│   ├── components/
│   │   ├── LoginPage.vue       # Страница входа
│   │   ├── HomePage.vue        # Главная (список товаров)
│   │   ├── AddProductPage.vue  # Добавление товара
│   │   └── StatusPage.vue      # Статус системы
│   ├── services/
│   │   └── auth.js             # Аутентификация + API
│   ├── utils/
│   │   └── apiConfig.js        # Определение API URL
│   ├── router/
│   │   └── index.js            # Vue Router
│   ├── App.vue
│   └── main.js
├── src/__tests__/              # Vitest тесты
│   ├── App.test.js
│   ├── auth.test.js
│   └── apiConfig.test.js
├── public/
├── index.html                  # Runtime API URL скрипт
├── nginx.conf                  # Nginx конфиг для SPA
├── Dockerfile                  # Multi-stage build
├── vite.config.js
├── package.json
└── .env.production             # VITE_API_URL для прода
```

### Важно: API URL определение

Vite агрессивно оптимизирует код при сборке. Для правильной работы на разных окружениях:

1. **index.html** - runtime скрипт ДО загрузки бандла:
```html
<script>
  (function() {
    var host = window.location.hostname;
    if (host === 'wh-lab.ru') {
      window.__API_URL__ = 'https://api.wh-lab.ru/api';
    } else if (host === '192.168.1.74') {
      window.__API_URL__ = 'http://192.168.1.74:30080/api';
    } else {
      window.__API_URL__ = 'http://' + host + ':30080/api';
    }
  })();
</script>
```

2. **auth.js** - использует `new Function()` для обхода оптимизации

---

## warehouse-master

**Назначение:** Оркестрация деплоя, K8s манифесты, CI/CD, инструменты

### Структура
```
warehouse-master/
├── .claude/
│   ├── project-context.md      # Контекст для AI агента
│   └── settings.local.json     # Настройки Claude Code
├── docs/
│   ├── ARCHITECTURE.md         # ← Этот файл
│   ├── INFRASTRUCTURE_GUIDE.md # Полная инвентаризация
│   ├── PROJECT_STATUS.md
│   ├── TROUBLESHOOTING_GUIDE.md
│   ├── BUGFIX_REPORT_*.md      # Отчёты об исправлениях
│   └── PLAN_PM_BOT.md          # План PM-бота для Telegram
├── k8s/
│   ├── warehouse/              # API + Frontend + PostgreSQL + доп. сервисы
│   │   ├── api-deployment.yaml
│   │   ├── api-service.yaml
│   │   ├── api-configmap.yaml
│   │   ├── api-secret.yaml
│   │   ├── api-servicemonitor.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── frontend-service.yaml
│   │   ├── frontend-ingress.yaml
│   │   ├── redis-deployment.yaml     # Redis для кэширования
│   │   ├── redis-service.yaml
│   │   ├── redis-configmap.yaml
│   │   ├── kafka-deployment.yaml     # Kafka KRaft (без Zookeeper)
│   │   ├── kafka-service.yaml
│   │   └── kafka-configmap.yaml
│   ├── loadtest/               # Locust нагрузочное тестирование
│   │   ├── namespace.yaml
│   │   ├── locust-configmap.yaml
│   │   ├── locust-deployment.yaml
│   │   └── locust-service.yaml
│   ├── notifications/          # Telegram Bot
│   │   ├── bot-deployment.yaml
│   │   ├── bot-service.yaml
│   │   └── bot-secret.yaml
│   └── monitoring/             # Prometheus + Grafana
│       ├── namespace.yaml
│       ├── prometheus-configmap.yaml
│       ├── prometheus-deployment.yaml
│       ├── prometheus-service.yaml
│       ├── prometheus-nodeport.yaml
│       ├── grafana-deployment.yaml   # Grafana с дашбордами
│       ├── grafana-service.yaml
│       ├── grafana-secret.yaml
│       ├── grafana-datasources.yaml
│       ├── grafana-dashboards-config.yaml
│       └── grafana-dashboards.yaml   # Warehouse API дашборд
├── telegram-bot/               # Telegram бот для уведомлений
│   ├── app.py                  # Точка входа
│   ├── config.py               # Все настройки
│   ├── bot/
│   │   ├── handlers/
│   │   │   ├── commands.py     # /start, /status, /help
│   │   │   ├── deploy.py       # Деплой команды
│   │   │   ├── testing.py      # Тесты и НТ
│   │   │   ├── claude.py       # AI интеграция
│   │   │   └── gitlab_webhook.py
│   │   ├── keyboards.py
│   │   ├── messages.py
│   │   └── telegram.py
│   ├── services/
│   │   ├── gitlab.py
│   │   ├── locust.py
│   │   ├── allure.py
│   │   └── health.py
│   ├── claude_proxy.py         # Прокси для Anthropic API
│   ├── test_payloads/          # Тестовые webhook payloads
│   └── Dockerfile
├── orchestrator-ui/            # 8-bit консоль управления
│   ├── app/
│   │   ├── main.py             # FastAPI приложение (WebSocket, webhook)
│   │   ├── agent.py            # Claude AI агент
│   │   ├── gitlab.py           # GitLab API
│   │   ├── services.py         # K8s статусы
│   │   ├── database.py         # SQLite история
│   │   └── config.py           # Конфигурация
│   ├── templates/              # Jinja2 шаблоны
│   │   ├── index.html
│   │   ├── notifications.html
│   │   └── partials/
│   ├── static/                 # CSS, JS
│   ├── docker-compose.yml
│   └── Dockerfile
├── loadtest/
│   └── locustfile.py           # Сценарий нагрузки
├── scripts/
│   ├── deploy-local.sh         # Локальный деплой в K3s
│   └── load-test.sh            # Запуск НТ
├── selenoid/                   # Selenoid (Docker Compose)
│   ├── docker-compose.yml
│   └── config/browsers.json
├── e2e-tests/                  # API E2E тесты (RestAssured)
│   └── src/test/java/com/warehouse/e2e/
│       ├── base/BaseE2ETest.java
│       ├── helpers/
│       ├── data/
│       └── tests/
├── ui-tests/                   # UI тесты (Selenide + Allure)
│   ├── pom.xml
│   └── src/test/java/com/warehouse/ui/
│       ├── config/
│       ├── pages/
│       └── tests/
├── .gitlab-ci.yml              # Главный пайплайн
└── README.md
```

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
│  │  ┌──────────────┐                                                  │   │
│  │  │ selenoid     │                                                  │   │
│  │  │ Deployment   │                                                  │   │
│  │  │ :4444→:30040 │                                                  │   │
│  │  └──────────────┘                                                  │   │
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
│  │  │ gitlab-telegram-bot             │                                │   │
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
│  │ selenoid + selenoid-ui                                                │  │
│  │ Ports: 4444 (Selenium Hub), 8090 (UI)                                │  │
│  │ URL: http://192.168.1.74:4444/wd/hub                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### NodePorts Summary (Staging)

| Service | NodePort | Internal | URL |
|---------|----------|----------|-----|
| warehouse-api | 30080 | 8080 | http://192.168.1.74:30080 |
| warehouse-frontend | 30081 | 80 | http://192.168.1.74:30081 |
| locust-master | 30089 | 8089 | http://192.168.1.74:30089 |
| telegram-bot-webhook | 30088 | 8000 | http://192.168.1.74:30088 |
| prometheus | 30090 | 9090 | http://192.168.1.74:30090 |
| grafana | 30300 | 3000 | http://192.168.1.74:30300 |

### Docker Compose сервисы (на хосте)

| Service | Port | URL |
|---------|------|-----|
| GitLab | 8080 | http://192.168.1.74:8080 |
| YouTrack | 8088 | http://192.168.1.74:8088 |
| Allure Server | 5050 | http://192.168.1.74:5050 |
| Allure UI | 5252 | http://192.168.1.74:5252 |
| Orchestrator UI | 8000 | http://192.168.1.74:8000 |
| Claude Proxy | 8765 | http://192.168.1.74:8765 |
| Selenoid | 4444 | http://192.168.1.74:4444/wd/hub |
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

### warehouse-api Pipeline
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  validate → build → test → package                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  validate:     mvnw validate                                                │
│  build:        mvnw compile                                                 │
│  test:         mvnw test (unit tests, H2 DB)                               │
│  package:      mvnw package -DskipTests                                     │
│                docker build                                                 │
│                docker push → Yandex Registry                                │
│                docker save → k3s ctr images import                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### warehouse-frontend Pipeline
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  build → package                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  build:        npm install && npm run build                                 │
│  package:      docker build (multi-stage: node → nginx)                     │
│                docker push → Yandex Registry                                │
│                docker save → k3s ctr images import                          │
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
│                                                                             │
│  PRODUCTION (SSH + docker compose):                                         │
│  • deploy-api-prod                                                          │
│  • deploy-frontend-prod                                                     │
│  • deploy-all-prod                                                          │
│                                                                             │
│  TESTING:                                                                   │
│  • run-e2e-tests (mvnw test + Allure upload)                               │
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
- **API:** http://192.168.1.74:5050
- **UI:** http://192.168.1.74:5252
- **Projects:**
  - `warehouse-api` - API тесты
  - `warehouse-ui` - UI тесты

### Locust Load Testing
- **UI:** http://192.168.1.74:30089
- **Workers:** 5 replicas (оптимизировано после НТ)
- **Target:** warehouse-api-service.warehouse.svc.cluster.local:8080
- **Результаты НТ (WH-103):**
  - Max Users (0% ошибок): **150**
  - Max RPS: **63**
  - Max Users (<2% ошибок): **350-400**
- **Сценарии:**
  - SuperUser (weight 1): все операции
  - AdminUser (weight 2): просмотр
  - ManagerUser (weight 3): просмотр
  - EmployeeUser (weight 5): создание товаров

---

## UI и E2E тестирование

### Selenoid (Docker на хосте)
- **Selenium Hub:** http://192.168.1.74:4444/wd/hub
- **Selenoid UI:** http://192.168.1.74:8090
- **VNC:** Включен для отладки
- **Браузеры:** Chrome 131.0, 130.0, Firefox 132.0

**Запуск Selenoid:**
```bash
cd selenoid && docker-compose up -d
```

### ui-tests/ (Selenide + Allure)
**Технологии:** Java 17, Selenide 7.0.4, JUnit 5, Allure 2.25.0

```
ui-tests/
├── src/test/java/com/warehouse/ui/
│   ├── config/
│   │   ├── TestConfig.java      # Owner конфиг
│   │   └── BaseTest.java        # Базовый класс (скриншоты включены!)
│   ├── pages/
│   │   ├── LoginPage.java       # Page Object
│   │   └── ProductsPage.java
│   └── tests/
│       ├── LoginTest.java
│       ├── ProductsTest.java
│       └── RoleAccessTest.java
├── pom.xml
└── mvnw
```

**Запуск UI тестов:**
```bash
cd ui-tests
mvn test -Dbase.url=http://192.168.1.74:30081 -Dselenoid.url=http://192.168.1.74:4444/wd/hub
```

**Allure отчёт со скриншотами:** http://192.168.1.74:5252/allure-docker-service/projects/warehouse-ui/reports/latest

### e2e-tests/ (RestAssured API тесты)
**Технологии:** Spring Boot Test, RestAssured, Allure, JUnit 5

```
e2e-tests/
├── src/test/java/com/warehouse/e2e/
│   ├── base/BaseE2ETest.java    # Базовый класс
│   ├── helpers/                  # Хелперы (Auth, Product)
│   ├── data/TestData.java       # Тестовые данные
│   └── tests/
│       ├── AuthControllerE2ETest.java
│       └── ProductControllerE2ETest.java
```

### CI Pipeline для тестов
```yaml
deploy-selenoid:        # Запуск Selenoid (Docker Compose)
run-ui-tests:           # Selenide UI тесты → Allure со скриншотами
run-e2e-tests:          # RestAssured API тесты
run-load-tests:         # Locust НТ
```

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
            │   │  :30089  → Locust                  │    │
            │   │  :30090  → Prometheus              │    │
            │   │  :30300  → Grafana                 │    │
            │   │  :30088  → Telegram Bot Webhook    │    │
            │   │                                     │    │
            │   │  Docker (host):                    │    │
            │   │  :8080   → GitLab                  │    │
            │   │  :8088   → YouTrack                │    │
            │   │  :5050   → Allure API              │    │
            │   │  :5252   → Allure UI               │    │
            │   │  :8000   → Orchestrator UI         │    │
            │   │  :8765   → Claude Proxy            │    │
            │   │  :4444   → Selenoid Hub            │    │
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
| `manager` | Менеджер склада | MANAGER | CRUD товаров |
| `employee` | Сотрудник склада | EMPLOYEE | Создание товаров |
| `ivanov` | Иванов Алексей Петрович | SUPER_USER | Все |
| `petrova` | Петрова Мария Сергеевна | ADMIN | Управление пользователями |
| `sidorov` | Сидоров Дмитрий Андреевич | MANAGER | CRUD товаров |
| `kozlova` | Козлова Анна Викторовна | EMPLOYEE | Создание товаров |

---

*Последнее обновление: 2025-11-30 (НТ WH-103 завершено, добавлены postgres-replica, selenoid в K8s)*
