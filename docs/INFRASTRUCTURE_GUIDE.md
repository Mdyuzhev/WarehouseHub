# Warehouse Project - Infrastructure Guide `v2025.12.03`

> Полная инвентаризация хозяйства. Храни как зеницу ока! Обновлено: 2025-12-03 (WH-379 Notification Service)

---

## ВАЖНО: Порядок работы

### При начале работы:
1. **Прочитать этот файл** (`INFRASTRUCTURE_GUIDE.md`) - понять где что лежит
2. **Изучить файл** `docs/ARCHITECTURE.md` - понять архитектуру проекта
3. **Проверить статус сервисов** - убедиться что всё работает

### После завершения User Story:
**ОБЯЗАТЕЛЬНО** провести полный аудит и обновить файлы:
- `docs/ARCHITECTURE.md` - структура и компоненты
- `docs/INFRASTRUCTURE_GUIDE.md` - этот файл
- `docs/TROUBLESHOOTING_GUIDE.md` - новые проблемы

---

## Оглавление

1. [Обзор архитектуры](#обзор-архитектуры)
2. [Репозитории](#репозитории)
3. [Staging окружение](#staging-окружение-local-k3s)
4. [Production окружение](#production-окружение-yandex-cloud)
5. [Новые компоненты](#новые-компоненты-wh-120-wh-121)
6. [Инфраструктурные сервисы](#инфраструктурные-сервисы)
7. [Учётные данные](#учётные-данные)
8. [CI/CD](#cicd)
9. [Полезные команды](#полезные-команды)

---

## Обзор архитектуры

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           STAGING (Local K3s)                            │
│  192.168.1.74                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  K8s Namespaces                                                   │   │
│  │  ├── warehouse:      API (2) + Frontend + PostgreSQL + Replica   │   │
│  │  │                   + Redis + Kafka + Robot + Analytics          │   │
│  │  │                   + Selenoid (PROD)                            │   │
│  │  ├── warehouse-dev:  API (1) + Frontend + PostgreSQL + Redis     │   │
│  │  │                   (DEV environment, WH-192)                    │   │
│  │  ├── loadtest:       Locust Master + Workers (5) + Exporter      │   │
│  │  ├── notifications:  Telegram Bot (v5.6)                          │   │
│  │  └── monitoring:     Prometheus + Grafana + Alertmanager          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Docker Compose (не в K8s)                                        │   │
│  │  ├── GitLab CE                                                   │   │
│  │  ├── YouTrack                                                    │   │
│  │  ├── Allure Server + UI                                          │   │
│  │  ├── Selenoid + Selenoid UI                                      │   │
│  │  ├── Claude Proxy                                                │   │
│  │  └── Orchestrator UI                                             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION (Yandex Cloud)                         │
│  130.193.44.34                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Docker Compose                                                   │   │
│  │  ├── warehouse-api     → https://api.wh-lab.ru                   │   │
│  │  ├── warehouse-frontend → https://wh-lab.ru                      │   │
│  │  ├── PostgreSQL                                                  │   │
│  │  └── Nginx (reverse proxy + Let's Encrypt)                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Репозитории

| Проект | Локальный путь | GitLab ID | Описание |
|--------|----------------|-----------|----------|
| **warehouse-master** | `/home/flomaster/warehouse-master` | 4 | CI/CD, K8s манифесты, оркестрация |
| **warehouse-api** | `/home/flomaster/warehouse-api` | 1 | Spring Boot 3.2 REST API |
| **warehouse-frontend** | `/home/flomaster/warehouse-frontend` | 3 | Vue.js 3.4 SPA |

### Структура warehouse-master
```
warehouse-master/
├── .claude/                # Claude Code настройки + audit
├── docs/                   # Документация
│   ├── ARCHITECTURE.md
│   ├── INFRASTRUCTURE_GUIDE.md  (этот файл)
│   ├── TROUBLESHOOTING_GUIDE.md
│   ├── DEPLOY_GUIDE.md
│   ├── CREDENTIALS.md
│   └── YOUTRACK_API.md
├── k8s/                    # Kubernetes манифесты
│   ├── warehouse/          # API + Frontend + Redis + Kafka + Selenoid
│   ├── robot/              # Warehouse Robot (WH-120)
│   ├── analytics/          # Analytics Service (WH-121)
│   ├── loadtest/           # Locust (master + 5 workers)
│   ├── notifications/      # Telegram Bot
│   └── monitoring/         # Prometheus + Grafana
├── warehouse-robot/        # Симулятор складских операций (WH-120)
├── analytics-service/      # Real-time Kafka аналитика (WH-121)
├── telegram-bot/           # Уведомления в Telegram (v5.4)
├── orchestrator-ui/        # 8-bit консоль управления
├── e2e-tests/              # API E2E тесты (RestAssured)
├── ui-tests/               # UI тесты (Selenide + Allure)
├── loadtest/               # Locust скрипты
├── selenoid/               # Selenoid Docker Compose
├── scripts/                # Bash скрипты деплоя
└── .gitlab-ci.yml          # Главный пайплайн
```

---

## Staging окружение (Local K3s)

**Host:** `192.168.1.74`

### K8s Services (namespace: warehouse)

| Сервис | Внутренний URL | NodePort | Replicas | Описание |
|--------|----------------|----------|----------|----------|
| **warehouse-api** | `warehouse-api-service.warehouse.svc.cluster.local:8080` | `30080` | 2 | Spring Boot API |
| **warehouse-frontend** | `warehouse-frontend-service.warehouse.svc.cluster.local:80` | `30081` | 1 | Vue.js Frontend |
| **warehouse-robot** | `warehouse-robot-service.warehouse.svc.cluster.local:8070` | `30070` | 1 | Robot симулятор (WH-120) |
| **analytics-service** | `analytics-service.warehouse.svc.cluster.local:8090` | `30091` | 1 | Kafka аналитика (WH-121) |
| **PostgreSQL** | `postgres-service.warehouse.svc.cluster.local:5432` | `30432` | 1 | Database (primary) |
| **PostgreSQL Replica** | `postgres-replica-service.warehouse.svc.cluster.local:5432` | - | 1 | Database (read replica) |
| **Redis** | `redis.warehouse.svc.cluster.local:6379` | - | 1 | Кэширование |
| **Kafka** | `kafka.warehouse.svc.cluster.local:9092` | - | 1 | Messaging (KRaft) |
| **Selenoid** | `selenoid.warehouse.svc.cluster.local:4444` | `30040` | 1 | Selenium Hub |

### K8s Services (namespace: loadtest)

| Сервис | Внутренний URL | NodePort | Replicas | Описание |
|--------|----------------|----------|----------|----------|
| **Locust Master** | `locust-master-service.loadtest.svc.cluster.local:8089` | `30089` | 1 | Load testing UI |
| **Locust Workers** | - | - | 5 | Рабочие узлы |
| **Locust Exporter** | `locust-exporter.loadtest.svc.cluster.local:9646` | - | 1 | Prometheus метрики |

### K8s Services (namespace: notifications)

| Сервис | Внутренний URL | NodePort | Replicas | Описание |
|--------|----------------|----------|----------|----------|
| **Telegram Bot** | `gitlab-telegram-bot.notifications.svc.cluster.local:8000` | `30088` | 1 | Bot v5.4, GitLab webhooks |

### K8s Services (namespace: monitoring)

| Сервис | Внутренний URL | NodePort | Описание |
|--------|----------------|----------|----------|
| **Prometheus** | `prometheus-service.monitoring.svc.cluster.local:9090` | `30090` | Metrics |
| **Grafana** | `grafana.monitoring.svc.cluster.local:3000` | `30300` | Визуализация |
| **Alertmanager** | `alertmanager.monitoring.svc.cluster.local:9093` | - | Алертинг |
| **Kube State Metrics** | - | - | K8s метрики |
| **Node Exporter** | - | - | Хост метрики |

### K8s Services (namespace: warehouse-dev) - WH-192

Development окружение для параллельной разработки. Изолировано от prod (warehouse namespace).

| Сервис | Внутренний URL | NodePort | Replicas | Описание |
|--------|----------------|----------|----------|----------|
| **Warehouse API (dev)** | `warehouse-api-service.warehouse-dev.svc.cluster.local:8080` | `31080` | 1 | REST API (dev) |
| **Warehouse Frontend (dev)** | `warehouse-frontend-service.warehouse-dev.svc.cluster.local:80` | `31081` | 1 | Vue.js SPA (dev) |
| **PostgreSQL (dev)** | `postgres.warehouse-dev.svc.cluster.local:5432` | `31432` | 1 | База данных (dev) |
| **Redis (dev)** | `redis.warehouse-dev.svc.cluster.local:6379` | `31379` | 1 | Кэш/сессии (dev) |

**ResourceQuota:** 4 CPU, 8Gi Memory

### Docker Compose сервисы (на хосте)

| Сервис | URL | Порт | Описание |
|--------|-----|------|----------|
| **GitLab CE** | http://192.168.1.74:8080 | 8080 | Git + CI/CD |
| **YouTrack** | http://192.168.1.74:8088 | 8088 | Issue tracker |
| **Allure Server** | http://192.168.1.74:5050 | 5050 | Test reports API |
| **Allure UI** | http://192.168.1.74:5252 | 5252 | Test reports UI |
| **Allure Public** | https://advertiser-dark-remaining-sail.trycloudflare.com | cloudflared | Публичный доступ |
| **Locust Public** | (cloudflared tunnel → localhost:30089) | cloudflared | Публичный доступ |
| **YouTrack Public** | https://shots-health-trader-done.trycloudflare.com | cloudflared | Публичный доступ |
| **Selenoid** | http://192.168.1.74:4444/wd/hub | 4444 | Selenium Hub |
| **Selenoid UI** | http://192.168.1.74:8090 | 8090 | Просмотр сессий |
| **Claude Proxy** | http://192.168.1.74:8765 | 8765 | Anthropic API proxy |
| **Orchestrator UI** | http://192.168.1.74:8000 | 8000 | 8-bit консоль |

---

## Production окружение (Yandex Cloud)

**Host:** `130.193.44.34`
**User:** `ubuntu`
**Путь:** `/opt/warehouse`

### Публичные URL

| Сервис | URL | Описание |
|--------|-----|----------|
| **API** | https://api.wh-lab.ru | REST API |
| **Frontend** | https://wh-lab.ru | Web UI |

### Docker Compose сервисы

```yaml
services:
  api:
    image: cr.yandex/crpf5fukf1ili7kudopb/warehouse-api:latest
    ports: 8080
  frontend:
    image: cr.yandex/crpf5fukf1ili7kudopb/warehouse-frontend:latest
    ports: 80
  analytics:
    image: cr.yandex/crpf5fukf1ili7kudopb/warehouse-analytics:latest
    ports: 8090
  kafka:
    image: bitnami/kafka:3.6
  redis:
    image: redis:7.4.7
  postgres:
    image: postgres:15-alpine
    ports: 5432
  nginx:
    # Reverse proxy + Let's Encrypt SSL
```

### Текущий статус Production (2025-12-02)

| Container | Status | Описание |
|-----------|--------|----------|
| warehouse-frontend | Up | OK |
| warehouse-api | Up | Health UP (PostgreSQL, Redis connected) |
| warehouse-analytics | Up | OK |
| warehouse-kafka | Up (healthy) | OK |
| warehouse-db | Up (healthy) | PostgreSQL |
| warehouse-redis | Up (healthy) | Redis 7.4.7 |
| nginx | Up | Reverse proxy |
| certbot | Up | Let's Encrypt auto-renewal |

### Yandex Container Registry

```
Registry: cr.yandex/crpf5fukf1ili7kudopb
Images:
  - warehouse-api:latest
  - warehouse-api:{commit-sha}
  - warehouse-frontend:latest
  - warehouse-frontend:{commit-sha}
```

---

## Новые компоненты (WH-120, WH-121)

### Warehouse Robot (WH-120)

**Описание:** Симулятор складских операций

| Параметр | Значение |
|----------|----------|
| **Расположение** | `/warehouse-robot/` |
| **Port** | 30070 |
| **Namespace** | warehouse |
| **Image** | warehouse-robot:latest |
| **Технологии** | Python 3.11, FastAPI 0.109.0, httpx, faker, schedule |

**Сценарии:**
- `receiving` — Приёмка товара (создание 3-7 SKU)
- `shipping` — Отгрузка (уменьшение 2-5 товаров)
- `inventory` — Инвентаризация (корректировка ±5)

**Скорости:** slow (3-5s), normal (1-3s), fast (0.3-1s)

**API Endpoints:**
| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/health` | GET | Health check |
| `/status` | GET | Текущий статус |
| `/stats` | GET | Статистика |
| `/start` | POST | Запуск сценария |
| `/stop` | POST | Остановка |
| `/schedule` | POST | Запланировать |
| `/scheduled` | GET | Список запланированных |
| `/scheduled/{id}` | DELETE | Отменить |

**Деплой:**
```bash
cd ~/warehouse-master/warehouse-robot
docker build --no-cache -t warehouse-robot:latest .
sudo k3s ctr images rm docker.io/library/warehouse-robot:latest 2>/dev/null || true
docker save warehouse-robot:latest | sudo k3s ctr images import -
kubectl apply -k ~/warehouse-master/k8s/robot/
```

### Analytics Service (WH-121)

**Описание:** Real-time Kafka аналитика с WebSocket

| Параметр | Значение |
|----------|----------|
| **Расположение** | `/analytics-service/` |
| **Port** | 30091 |
| **Namespace** | warehouse |
| **Image** | analytics-service:latest |
| **Технологии** | Python 3.11, FastAPI 0.109.0, aiokafka 0.10.0, aioredis |

**Kafka Topics:**
- `warehouse.audit` — События аудита
- `warehouse.notifications` — Уведомления о низких остатках

**API Endpoints:**
| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/health` | GET | Health check (Kafka + Redis) |
| `/api/stats` | GET | Агрегированная статистика |
| `/api/events` | GET | Последние события (limit 100) |
| `/api/hourly` | GET | Почасовая статистика (168 часов) |
| `/api/daily` | GET | Дневная статистика (30 дней) |
| `/api/categories` | GET | По категориям |
| `/ws` | WS | Real-time события |

**Деплой:**
```bash
cd ~/warehouse-master/analytics-service
docker build --no-cache -t analytics-service:latest .
sudo k3s ctr images rm docker.io/library/analytics-service:latest 2>/dev/null || true
docker save analytics-service:latest | sudo k3s ctr images import -
kubectl apply -k ~/warehouse-master/k8s/analytics/
```

### Telegram Bot (v5.6)

**Расположение:** `/telegram-bot/`
**Port:** 30088
**Технологии:** Python 3.11, FastAPI 0.109.0, httpx

**Handlers:**
| Handler | Описание |
|---------|----------|
| `commands` | /start, /help, /status, /health, /metrics, /pods, /release |
| `deploy` | Деплой staging/production |
| `testing` | QA меню — E2E, UI тесты, Load testing |
| `claude` | AI интеграция |
| `pm` | PM Dashboard (YouTrack) |
| `robot` | Robot control + schedule |
| `gitlab_webhook` | GitLab webhooks |

**Деплой:**
```bash
cd ~/warehouse-master/telegram-bot
docker build --no-cache -t gitlab-telegram-bot:v5.6 .
sudo k3s ctr images rm docker.io/library/gitlab-telegram-bot:v5.6 2>/dev/null || true
docker save gitlab-telegram-bot:v5.6 | sudo k3s ctr images import -
kubectl apply -f ~/warehouse-master/k8s/notifications/
kubectl rollout restart deployment/gitlab-telegram-bot -n notifications
```

---

## Инфраструктурные сервисы

### Selenoid (браузеры для тестов)

**Docker Compose (хост):**
- **Hub:** http://192.168.1.74:4444/wd/hub
- **UI:** http://192.168.1.74:8090

**K8s (warehouse):**
- **Hub:** http://192.168.1.74:30040

**Браузеры (browsers.json):**
- Chrome 127.0, 128.0
- Firefox 125.0

### Cloudflared Tunnels (публичный доступ извне)

**Cloudflared** позволяет открыть локальные сервисы в интернет без белого IP и VPN.

**Текущие туннели:**

| Сервис | Локальный порт | Публичный URL |
|--------|----------------|---------------|
| Allure Server | localhost:5050 | https://advertiser-dark-remaining-sail.trycloudflare.com |
| Locust | localhost:30089 | (динамический URL) |
| YouTrack | localhost:8088 | https://shots-health-trader-done.trycloudflare.com |

**Как создать новый туннель:**

```bash
# Скачать cloudflared (если нет)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
chmod +x /tmp/cloudflared

# Запустить туннель (получит случайный URL *.trycloudflare.com)
/tmp/cloudflared tunnel --url http://localhost:PORT &

# Проверить что работает
ps aux | grep cloudflared

# Посмотреть URL в логах
# INF | Your quick Tunnel has been created! Visit it at: https://xxx.trycloudflare.com
```

**Важно:**
- URL меняется при каждом перезапуске туннеля (quick tunnel)
- Для постоянного URL нужен Cloudflare аккаунт и named tunnel
- Туннели работают в фоне, но умирают после перезагрузки сервера

---

### Allure Report Server

**Проекты:**
| Project ID | Описание |
|------------|----------|
| `e2e-staging` | E2E тесты на staging |
| `e2e-prod` | E2E тесты на production |
| `ui-staging` | UI тесты на staging |
| `ui-prod` | UI тесты на production |

**URL структура:**
```
http://192.168.1.74:5050/allure-docker-service/projects/{project}/reports/latest/index.html
```

**Публичный доступ (cloudflared):**
```
https://advertiser-dark-remaining-sail.trycloudflare.com
```

---

## Учётные данные

> **ВАЖНО:** Эти данные конфиденциальны. Не коммить в публичные репозитории!

### PostgreSQL (Staging - K8s)

| Параметр | Значение |
|----------|----------|
| **Host** | `postgres-service.warehouse.svc.cluster.local` |
| **Port** | `5432` |
| **External Port** | `30432` |
| **Database** | `warehouse` |
| **Admin User** | `postgres` |
| **Admin Password** | `postgres_admin_2025` |
| **App User** | `warehouse_user` |
| **App Password** | `warehouse_secret_2025` |
| **JDBC URL** | `jdbc:postgresql://postgres-service.warehouse.svc.cluster.local:5432/warehouse` |

### JWT Secret (Staging)

```
BcxfC7EDiXdnfjCdjdIRrntE7heN1RcvA/3pnHCT1kw=
```

### Telegram Bot

| Параметр | Значение |
|----------|----------|
| **Bot Token** | `8532494921:AAEoxQ87qQVcutgCSa8d8DntT_47xhvrCAI` |
| **Chat ID** | `290274837` |
| **Webhook Secret** | `warehouse-webhook-secret-2024` |

### GitLab

| Параметр | Значение |
|----------|----------|
| **URL** | http://192.168.1.74:8080 |
| **User** | root |
| **Password** | Misha2021@1@ |
| **Personal Access Token** | `glpat-Ou0qfvnfGfUOGkbs3nmv8m86MQp1OjEH.01.0w0ojabq3` |

### YouTrack

| Параметр | Значение |
|----------|----------|
| **URL** | http://192.168.1.74:8088 |
| **Public URL** | https://shots-health-trader-done.trycloudflare.com |
| **Project ID** | `0-1` |
| **Project Short** | `WH` |
| **User** | `admin` |
| **Password** | `Misha2021@1@` |
| **Auth** | **ТОЛЬКО Basic Auth!** |

**Read-only пользователь (для демо):**

| Параметр | Значение |
|----------|----------|
| **Login** | `demo` |
| **Password** | `demo` |
| **Role** | Observer (только чтение) |
| **Доступ** | Проект WH + Dashboard |

### Deploy Passwords (Telegram Bot)

| Параметр | Значение |
|----------|----------|
| **Deploy Password** | `Misha2021@1@` |
| **Load Test Password** | `Misha2021@1@` |
| **Robot Password** | (в K8s secrets) |
| **Guest Password** | `Guest` |

### Grafana

| Параметр | Значение |
|----------|----------|
| **URL** | http://192.168.1.74:30300 |
| **User** | `admin` |
| **Password** | `admin123` |

### Yandex Cloud Registry Auth

```
Ключ: /home/flomaster/secrets/yc-registry-key.json
Логин: json_key
```

---

## Тестовые пользователи (Warehouse API)

> Пароль для всех: `password123`

| Username | Full Name | Role | Права |
|----------|-----------|------|-------|
| `superuser` | Суперпользователь | SUPER_USER | Все |
| `admin` | Администратор | ADMIN | Управление пользователями |
| `manager` | Менеджер склада | MANAGER | Просмотр товаров |
| `employee` | Сотрудник склада | EMPLOYEE | CRUD товаров |
| `analyst` | Аналитик | ANALYST | Только аналитика (WH-121) |
| `ivanov` | Иванов Алексей Петрович | SUPER_USER | Все |
| `petrova` | Петрова Мария Сергеевна | ADMIN | Управление пользователями |
| `sidorov` | Сидоров Дмитрий Андреевич | MANAGER | Просмотр товаров |
| `kozlova` | Козлова Анна Викторовна | EMPLOYEE | CRUD товаров |

---

## CI/CD

### GitLab Runners

- **Shell executor** на `192.168.1.74`
- Tag: `shell`

### Dual Environment Pipeline (WH-200)

С декабря 2025 настроен dual environment workflow:

| Ветка | Окружение | Namespace | Порты | Деплой |
|-------|-----------|-----------|-------|--------|
| `develop` | Development | `warehouse-dev` | 31xxx | **Автоматический** |
| `main` | Production | `warehouse` | 30xxx | **Ручной (manual)** |

### Pipeline Flow

```
warehouse-api (develop branch):
  validate → build → test → package → deploy-dev (auto)
  ↓
  Docker image → Registry → K3s → warehouse-dev namespace

warehouse-api (main branch):
  validate → build → test → package → deploy-prod (manual)
  ↓
  Docker image → Registry → K3s → warehouse namespace

warehouse-frontend (develop branch):
  test → build → package → deploy-dev (auto)
  ↓
  Docker image → Registry → K3s → warehouse-dev namespace

warehouse-frontend (main branch):
  test → build → package → deploy-prod (manual)
  ↓
  Docker image → Registry → K3s → warehouse namespace

warehouse-master (оркестрация):
  deploy-staging (manual):
    - deploy-api-staging
    - deploy-frontend-staging
    - deploy-all-staging
    - deploy-telegram-bot
    - deploy-orchestrator-ui
    - deploy-robot
    - deploy-analytics
  deploy-prod (manual):
    - deploy-api-prod
    - deploy-frontend-prod
    - deploy-all-prod
  test (manual):
    - run-e2e-tests-staging
    - run-e2e-tests-prod
    - run-ui-tests-staging
    - run-ui-tests-prod
    - run-load-tests
```

### GitLab Environments

| Environment | API URL | Frontend URL | Описание |
|-------------|---------|--------------|----------|
| **development** | http://192.168.1.74:31080 | http://192.168.1.74:31081 | Dev окружение для develop |
| **production** | http://192.168.1.74:30080 | http://192.168.1.74:30081 | Prod окружение для main |

### Allure Reports после тестов

| Job | Project ID | URL |
|-----|------------|-----|
| run-e2e-tests-staging | e2e-staging | http://192.168.1.74:5252/#/projects/e2e-staging |
| run-e2e-tests-prod | e2e-prod | http://192.168.1.74:5252/#/projects/e2e-prod |
| run-ui-tests-staging | ui-staging | http://192.168.1.74:5252/#/projects/ui-staging |
| run-ui-tests-prod | ui-prod | http://192.168.1.74:5252/#/projects/ui-prod |

---

## Полезные команды

### Kubernetes

```bash
# Статус всех подов
kubectl get pods -A

# Логи API (последние 100 строк)
kubectl logs -n warehouse -l app=warehouse-api --tail=100 -f

# Логи Robot
kubectl logs -n warehouse -l app=warehouse-robot -f

# Логи Analytics
kubectl logs -n warehouse -l app=analytics-service -f

# Логи Telegram Bot
kubectl logs -n notifications -l app=gitlab-telegram-bot -f

# Перезапуск API
kubectl rollout restart deployment/warehouse-api -n warehouse

# Перезапуск Robot
kubectl delete pod -n warehouse -l app=warehouse-robot

# Секреты
kubectl get secrets -n warehouse -o yaml

# Описание пода
kubectl describe pod -n warehouse -l app=warehouse-api
```

### Docker (Staging host)

```bash
# Статус сервисов
docker ps

# Логи GitLab
docker logs gitlab -f

# Логи YouTrack
docker logs youtrack -f

# Логи Allure
docker logs allure -f
```

### Production деплой

```bash
# SSH на прод
ssh -i ~/.ssh/yc_prod_key ubuntu@130.193.44.34

# На проде
cd /opt/warehouse
sudo docker compose pull
sudo docker compose up -d
sudo docker image prune -f
```

### Health checks

```bash
# API Staging
curl -s http://192.168.1.74:30080/actuator/health | jq

# API Prod
curl -s https://api.wh-lab.ru/actuator/health | jq

# Robot
curl -s http://192.168.1.74:30070/health | jq

# Analytics
curl -s http://192.168.1.74:30091/health | jq

# Frontend (статус код)
curl -s http://192.168.1.74:30081/ -o /dev/null -w "%{http_code}"

# Telegram Bot
curl -s http://192.168.1.74:30088/health -o /dev/null -w "%{http_code}"
```

### K3s / containerd

```bash
# Список образов в K3s
sudo k3s ctr images list | grep warehouse

# Импорт образа в K3s
docker save IMAGE:TAG | sudo k3s ctr images import -

# Удаление образа из K3s
sudo k3s ctr images rm docker.io/library/IMAGE:TAG
```

### YouTrack API

```bash
# Получить задачу
curl -s -u 'admin:Misha2021@1@' 'http://192.168.1.74:8088/api/issues/WH-XXX'

# Добавить комментарий
curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/issues/WH-XXX/comments' \
  -H 'Content-Type: application/json' \
  -d '{"text":"Комментарий"}'
```

### Нагрузочное тестирование

```bash
# Через Telegram Bot
# Кнопка "🔬 QA" → "🧪 STAGING" → "🔥 Нагрузочное"

# Или через Locust UI
# http://192.168.1.74:30089
```

---

## Быстрые ссылки

| Что | Куда |
|-----|------|
| **Staging API** | http://192.168.1.74:30080/swagger-ui.html |
| **Staging Frontend** | http://192.168.1.74:30081 |
| **Staging Analytics** | http://192.168.1.74:30081/analytics |
| **Staging Robot** | http://192.168.1.74:30070 |
| **Production API** | https://api.wh-lab.ru/swagger-ui.html |
| **Production Frontend** | https://wh-lab.ru |
| **GitLab** | http://192.168.1.74:8080 |
| **YouTrack** | http://192.168.1.74:8088 |
| **Allure Reports** | http://192.168.1.74:5252 |
| **Allure Public** | https://advertiser-dark-remaining-sail.trycloudflare.com |
| **Locust** | http://192.168.1.74:30089 |
| **YouTrack Public** | https://shots-health-trader-done.trycloudflare.com |
| **Prometheus** | http://192.168.1.74:30090 |
| **Grafana** | http://192.168.1.74:30300 |
| **Selenoid (Docker)** | http://192.168.1.74:4444/wd/hub |
| **Selenoid (K8s)** | http://192.168.1.74:30040 |
| **Selenoid UI** | http://192.168.1.74:8090 |
| **Orchestrator UI** | http://192.168.1.74:8000 |

---

## Актуальный статус (2025-12-03)

| Namespace | Deployments | Status |
|-----------|-------------|--------|
| warehouse | warehouse-api (2), frontend, robot, analytics, postgres, postgres-replica, redis, kafka, selenoid | ✅ All Running |
| warehouse-dev | warehouse-api (1), frontend, postgres, redis | ✅ All Running |
| loadtest | locust-master, locust-worker (5), locust-exporter, k6-notification-test | ✅ Running |
| notifications | gitlab-telegram-bot (v5.6) | ✅ Running |
| monitoring | prometheus, grafana, alertmanager, kube-state-metrics, node-exporter | ✅ All Running |

---

## Конфигурация через .env (WH-183)

Все сервисы имеют `.env.example` шаблоны:

| Сервис | Файл | Переменные |
|--------|------|------------|
| telegram-bot | `telegram-bot/.env.example` | BOT_*, GITLAB_*, ALLURE_*, YOUTRACK_* |
| warehouse-robot | `warehouse-robot/.env.example` | ROBOT_API_*, ROBOT_*_USERNAME/PASSWORD |
| analytics-service | `analytics-service/.env.example` | ANALYTICS_KAFKA_*, ANALYTICS_REDIS_* |

**Использование:**
```bash
cd telegram-bot && cp .env.example .env && vim .env
```

---

## Защита секретов (WH-184)

В `.gitignore` добавлена защита:

```gitignore
# Environment files
.env
*.env.local
!.env.example

# Credentials
credentials.json
secrets.yaml
*.pem, *.key, *.crt

# K8s secrets
*-secret.yaml.local

# Test properties
**/test.properties
!**/test.properties.example
```

---

*Последнее обновление: 2025-12-03 (Ревизия после WH-379 Notification Service)*
