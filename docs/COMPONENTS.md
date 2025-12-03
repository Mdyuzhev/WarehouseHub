# Components Guide `v2025.12.03`

Описание всех компонентов системы Warehouse.

## Репозитории

| Репозиторий | Путь | GitLab URL | Технологии |
|-------------|------|------------|------------|
| warehouse-api | `/home/flomaster/warehouse-api` | http://192.168.1.74:8080/root/warehouse-api.git | Java 17 + Spring Boot 3.2.0 |
| warehouse-frontend | `/home/flomaster/warehouse-frontend` | http://192.168.1.74:8080/root/warehouse-frontend.git | Vue.js 3.4 + Vite 5 |
| warehouse-master | `/home/flomaster/warehouse-master` | http://192.168.1.74:8080/root/warehouse-master.git | CI/CD, K8s manifests, Bot, Scripts |

---

## Основные сервисы

### Warehouse API

| Параметр | Значение |
|----------|----------|
| Технологии | Java 17 + Spring Boot 3.2.0 |
| Port (Staging) | 30080 |
| Port (Dev) | 31080 |
| Replicas | 2 (prod), 1 (dev) |
| Namespace | warehouse / warehouse-dev |
| Image | warehouse-api:latest |

**Зависимости:**
- PostgreSQL (JWT tokens, данные)
- Redis (кэширование, rate limiting, token blacklist)
- Kafka (audit events, notifications)

**Endpoints (31 total):**
- `/api/auth/*` - аутентификация (4)
- `/api/products/*` - CRUD товаров (5)
- `/api/facilities/*` - управление объектами (8, WH-269)
- `/api/stock/*` - управление остатками (8, WH-270)
- `/api/notifications/*` - уведомления (3, WH-379)
- `/actuator/health` - health check
- `/actuator/prometheus` - метрики
- `/swagger-ui.html` - Swagger UI

---

### Warehouse Frontend

| Параметр | Значение |
|----------|----------|
| Технологии | Vue.js 3.4 + Vite 5 + Vue Router 4 |
| Port (Staging) | 30081 |
| Port (Dev) | 31081 |
| Replicas | 1 |
| Namespace | warehouse / warehouse-dev |
| Image | warehouse-frontend:latest |

**Страницы:**
- `/login` - авторизация
- `/` - список товаров
- `/add` - добавление товара
- `/status` - статус системы (ADMIN)
- `/analytics` - аналитика (ANALYST+)

---

### Warehouse Robot (WH-120)

| Параметр | Значение |
|----------|----------|
| Технологии | Python 3.11 + FastAPI 0.109.0 |
| Port | 30070 |
| Replicas | 1 |
| Namespace | warehouse |
| Image | warehouse-robot:latest |
| Расположение | `/warehouse-robot/` |

**Сценарии:**

| Сценарий | Описание |
|----------|----------|
| `receiving` | Приёмка товара (создание 3-7 SKU) |
| `shipping` | Отгрузка (уменьшение 2-5 товаров) |
| `inventory` | Инвентаризация (корректировка ±5) |

**Скорости:** `slow` (3-5s), `normal` (1-3s), `fast` (0.3-1s)

**API:**
- `GET /health` - health check
- `GET /status` - текущий статус
- `GET /stats` - статистика
- `POST /start` - запуск сценария
- `POST /stop` - остановка
- `POST /schedule` - запланировать
- `GET /scheduled` - список запланированных

---

### Analytics Service (WH-121)

| Параметр | Значение |
|----------|----------|
| Технологии | Python 3.11 + FastAPI 0.109.0 + aiokafka |
| Port | 30091 |
| Replicas | 1 |
| Namespace | warehouse |
| Image | analytics-service:latest |
| Расположение | `/analytics-service/` |

**Kafka Topics:**
- `warehouse.audit` - события аудита
- `warehouse.notifications` - уведомления склада

**API:**
- `GET /health` - health check (Kafka + Redis)
- `GET /api/stats` - агрегированная статистика
- `GET /api/events` - последние события
- `GET /api/hourly` - почасовая статистика
- `GET /api/daily` - дневная статистика
- `WS /ws` - real-time события

---

### Notification Service (WH-379)

| Параметр | Значение |
|----------|----------|
| Технологии | Spring Boot 3.2.0 (часть warehouse-api) |
| Endpoints | `/api/notifications/*` (3 endpoint) |
| Channels | TELEGRAM, EMAIL, WEBHOOK, IN_MEMORY |
| Statuses | PENDING, SENDING, SENT, FAILED, DEAD |

**API:**
- `POST /api/notifications` - создать уведомление
- `GET /api/notifications/{id}` - получить по ID
- `GET /api/notifications/stats` - статистика

**Telegram Integration:**
- Bot: @wh_ntf_bot
- Chat: WH_lab_notify (-1003231635846)
- Формат: HTML с bold для subject

---

### Stock API (WH-270)

| Параметр | Значение |
|----------|----------|
| Технологии | Spring Boot 3.2.0 (часть warehouse-api) |
| Endpoints | `/api/stock/*` (8 endpoints) |
| Flyway | V4__add_stock_table.sql |
| Kafka | События в warehouse.audit |

**Endpoints:**

| Endpoint | Метод | Описание | Роли |
|----------|-------|----------|------|
| `/api/stock/facility/{id}` | GET | Все остатки на объекте | EMPLOYEE+ |
| `/api/stock/product/{id}` | GET | Остатки товара на всех объектах | EMPLOYEE+ |
| `/api/stock/product/{id}/facility/{id}` | GET | Конкретный остаток | EMPLOYEE+ |
| `/api/stock/product/{id}/total` | GET | Суммарный остаток товара | EMPLOYEE+ |
| `/api/stock/product/{id}/facility/{id}` | POST | Установить остаток | MANAGER+ |
| `/api/stock/product/{id}/facility/{id}/adjust` | PATCH | Изменить остаток (±) | EMPLOYEE+ |
| `/api/stock/product/{id}/facility/{id}/reserve` | POST | Зарезервировать | EMPLOYEE+ |
| `/api/stock/facility/{id}/low` | GET | Товары с низким остатком | MANAGER+ |

**Stock DTO:**
```json
{
  "id": 1,
  "productId": 1,
  "productName": "Ключ разводной",
  "facilityId": 1,
  "facilityCode": "DC-001",
  "facilityName": "Test DC",
  "quantity": 150,
  "reserved": 25,
  "available": 125
}
```

---

### Telegram Bot (v5.6)

| Параметр | Значение |
|----------|----------|
| Технологии | Python 3.11 + FastAPI + aiogram |
| Port | 30088 |
| Replicas | 1 |
| Namespace | notifications |
| Image | gitlab-telegram-bot:v5.6 |
| Расположение | `/telegram-bot/` |

**Handlers:**

| Handler | Описание |
|---------|----------|
| commands | /start, /help, /status, /health, /metrics, /pods, /release |
| deploy | Деплой staging/production |
| testing | QA меню, Load Testing Wizard (7 шагов), Locust/k6 |
| cleanup | Очистка Redis/Kafka/PostgreSQL |
| claude | AI интеграция |
| pm | PM Dashboard (YouTrack) |
| robot | Robot control + schedule |
| gitlab_webhook | GitLab webhooks |

**WH-217 (v5.6):**
- Load Testing Wizard — 7 шагов (среда → пароль → сценарий → VU → время → паттерн → confirm)
- Cleanup Service — Redis FLUSHDB, Kafka consumer groups, PostgreSQL тестовые данные
- Cooldown 30 минут между нагрузочными тестами
- k6 Kafka для Production (KAFKA_PROD_BROKERS: 130.193.44.34:29092)
- k6 Notification Load Test (WH-396)

---

## Инфраструктурные сервисы

### PostgreSQL

| Параметр | Prod (warehouse) | Dev (warehouse-dev) |
|----------|------------------|---------------------|
| Type | StatefulSet | Deployment |
| Port (internal) | 5432 | 5432 |
| Port (external) | 30432 | 31432 |
| Database | warehouse | warehouse_dev |
| User | warehouse_user | warehouse_user |
| Password | warehouse_secret_2025 | warehouse_secret_2025 |

### Redis

| Параметр | Prod (warehouse) | Dev (warehouse-dev) |
|----------|------------------|---------------------|
| Port (internal) | 6379 | 6379 |
| Port (external) | - | 31379 |
| Version | 7.4.7 | 7.4.7 |

**Ключи Redis:**

| Pattern | TTL | Назначение |
|---------|-----|------------|
| `rate_limit:login:*` | 15 мин | Rate limiting |
| `jwt_blacklist:*` | до exp | Blacklisted tokens |
| `auth:token:*` | 1 час | Кэш JWT |
| `products` | 5 мин | Кэш товаров |

### Kafka (KRaft)

| Параметр | Staging | Production |
|----------|---------|------------|
| Port (internal) | 9092 | 9092 |
| Port (external) | - | 29092 |
| Mode | KRaft (без Zookeeper) | KRaft (без Zookeeper) |
| Host | kafka.warehouse.svc.cluster.local | 130.193.44.34 |
| Topics | warehouse.audit, warehouse.notifications | warehouse.audit, warehouse.notifications |
| Partitions | 3 | 3 |

---

## Мониторинг

### Prometheus

| Параметр | Значение |
|----------|----------|
| Port | 30090 |
| Namespace | monitoring |
| URL | http://192.168.1.74:30090 |

### Grafana

| Параметр | Значение |
|----------|----------|
| Port | 30300 |
| Namespace | monitoring |
| URL | http://192.168.1.74:30300 |
| User | admin |
| Password | admin123 |

**Дашборды:**

| Dashboard | UID | Описание |
|-----------|-----|----------|
| Warehouse API | - | JVM, HTTP, HikariCP |
| Integration Load Testing | integration-load-testing | Locust + API + Kafka |
| Kafka Load Testing | kafka-load-testing | k6 Kafka metrics |

### Alertmanager

| Параметр | Значение |
|----------|----------|
| Port | 9093 |
| Namespace | monitoring |

---

## Load Testing

### Locust

| Параметр | Значение |
|----------|----------|
| Port | 30089 |
| Namespace | loadtest |
| Master replicas | 1 |
| Worker replicas | 5 |
| URL | http://192.168.1.74:30089 |

### k6-operator

| Параметр | Значение |
|----------|----------|
| Namespace | loadtest |
| Image | k6-kafka:latest |
| Workers | 6 (distributed) |

---

## Тестирование

### Selenoid

| Параметр | Docker | K8s |
|----------|--------|-----|
| Hub URL | http://192.168.1.74:4444/wd/hub | http://192.168.1.74:30040 |
| UI URL | http://192.168.1.74:8090 | - |
| Browsers | Chrome 127/128, Firefox 125 | Chrome 127/128, Firefox 125 |

### Allure

| Параметр | Значение |
|----------|----------|
| API URL | http://192.168.1.74:5050 |
| UI URL | http://192.168.1.74:5252 |
| Public URL | https://advertiser-dark-remaining-sail.trycloudflare.com |

**Проекты:**

| Project ID | Описание |
|------------|----------|
| e2e-staging | E2E тесты на staging |
| e2e-prod | E2E тесты на production |
| ui-staging | UI тесты на staging |
| ui-prod | UI тесты на production |

---

## DevOps сервисы

### GitLab

| Параметр | Значение |
|----------|----------|
| URL | http://192.168.1.74:8080 |
| User | root |
| Password | Misha2021@1@ |

### YouTrack

| Параметр | Значение |
|----------|----------|
| URL | http://192.168.1.74:8088 |
| Public URL | https://shots-health-trader-done.trycloudflare.com |
| Project | WH (ID: 0-1) |
| Auth | **ТОЛЬКО Basic Auth!** |
| User | admin |
| Password | Misha2021@1@ |

---

## Production (Yandex Cloud)

| Параметр | Значение |
|----------|----------|
| Host | 130.193.44.34 |
| User | ubuntu |
| Path | /opt/warehouse |
| API URL | https://api.wh-lab.ru |
| Frontend URL | https://wh-lab.ru |

**Containers:**
- api, frontend, analytics
- kafka, redis, db
- nginx, certbot

---

## .env файлы

Все Python сервисы имеют `.env.example` шаблоны:

| Сервис | Файл | Переменные |
|--------|------|------------|
| telegram-bot | `.env.example` | BOT_*, GITLAB_*, ALLURE_*, YOUTRACK_* |
| warehouse-robot | `.env.example` | ROBOT_API_*, ROBOT_*_USERNAME/PASSWORD |
| analytics-service | `.env.example` | ANALYTICS_KAFKA_*, ANALYTICS_REDIS_* |

**Использование:**
```bash
cp .env.example .env
vim .env
```

---

## Деплой

### Staging (K3s)

```bash
# API
cd ~/warehouse-api
docker build --no-cache -t warehouse-api:latest .
sudo k3s ctr images rm docker.io/library/warehouse-api:latest 2>/dev/null || true
docker save warehouse-api:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/warehouse-api -n warehouse

# Robot
cd ~/warehouse-master/warehouse-robot
docker build --no-cache -t warehouse-robot:latest .
docker save warehouse-robot:latest | sudo k3s ctr images import -
kubectl apply -k ~/warehouse-master/k8s/robot/

# Analytics
cd ~/warehouse-master/analytics-service
docker build --no-cache -t analytics-service:latest .
docker save analytics-service:latest | sudo k3s ctr images import -
kubectl apply -k ~/warehouse-master/k8s/analytics/

# Telegram Bot
cd ~/warehouse-master/telegram-bot
docker build --no-cache -t gitlab-telegram-bot:v5.6 .
docker save gitlab-telegram-bot:v5.6 | sudo k3s ctr images import -
kubectl rollout restart deployment/gitlab-telegram-bot -n notifications
```

### Production

```bash
ssh -i ~/.ssh/yc_prod_key ubuntu@130.193.44.34 'cd /opt/warehouse && sudo docker compose pull && sudo docker compose up -d'
```

---

*Последнее обновление: 2025-12-03*
