# Warehouse Project - Infrastructure Guide

> Полная инвентаризация хозяйства. Храни как зеницу ока! Обновлено: 2025-12-01 (WH-155 QA)

---

## ВАЖНО: Порядок работы

### При начале работы:
1. **Прочитать этот файл** (`INFRASTRUCTURE_GUIDE.md`) - понять где что лежит
2. **Изучить файл** `docs/ARCHITECTURE.md` - понять архитектуру проекта

### После завершения User Story:
**ОБЯЗАТЕЛЬНО** провести полный аудит и обновить файл `docs/ARCHITECTURE.md`:
- Проверить актуальность всех схем и описаний
- Обновить структуру файлов если были изменения
- Добавить новые компоненты/сервисы
- Обновить дату в конце файла

---

## Оглавление

1. [Обзор архитектуры](#обзор-архитектуры)
2. [Репозитории](#репозитории)
3. [Staging окружение](#staging-окружение-local-k3s)
4. [Production окружение](#production-окружение-yandex-cloud)
5. [Новые компоненты (WH-120, WH-121)](#новые-компоненты-wh-120-wh-121)
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
│  │  │                   + Selenoid                                   │   │
│  │  ├── loadtest:       Locust Master + Workers (5)                  │   │
│  │  ├── notifications:  Telegram Bot (v5.4)                          │   │
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
| **warehouse-api** | `/home/flomaster/warehouse-api` | 1 | Spring Boot REST API |
| **warehouse-frontend** | `/home/flomaster/warehouse-frontend` | 3 | Vue.js SPA |

### Структура warehouse-master
```
warehouse-master/
├── .claude/                # Claude Code настройки + audit
├── docs/                   # Документация
├── e2e-tests/              # API E2E тесты (RestAssured)
├── ui-tests/               # UI тесты (Selenide + Allure)
├── selenoid/               # Selenoid Docker Compose
├── k8s/                    # Kubernetes манифесты
│   ├── warehouse/          # API + Frontend + Redis + Kafka
│   ├── robot/              # Warehouse Robot (WH-120)
│   ├── analytics/          # Analytics Service (WH-121)
│   ├── loadtest/           # Locust
│   ├── notifications/      # Telegram Bot
│   └── monitoring/         # Prometheus + Grafana
├── warehouse-robot/        # Симулятор складских операций (WH-120)
├── analytics-service/      # Real-time Kafka аналитика (WH-121)
├── telegram-bot/           # Уведомления в Telegram (v5.4)
├── orchestrator-ui/        # 8-bit консоль управления
├── loadtest/               # Locust скрипты
└── scripts/                # Bash скрипты деплоя
```

---

## Staging окружение (Local K3s)

**Host:** `192.168.1.74`

### K8s Services (namespace: warehouse)

| Сервис | Внутренний URL | NodePort | Описание |
|--------|----------------|----------|----------|
| **warehouse-api** | `warehouse-api-service.warehouse.svc.cluster.local:8080` | `30080` | Spring Boot API (2 replicas) |
| **warehouse-frontend** | `warehouse-frontend-service.warehouse.svc.cluster.local:80` | `30081` | Vue.js Frontend |
| **warehouse-robot** | `warehouse-robot-service.warehouse.svc.cluster.local:8070` | `30070` | Robot симулятор (WH-120) |
| **analytics-service** | `analytics-service.warehouse.svc.cluster.local:8090` | `30091` | Kafka аналитика (WH-121) |
| **PostgreSQL** | `postgres-service.warehouse.svc.cluster.local:5432` | `30432` | Database (primary) |
| **PostgreSQL Replica** | `postgres-replica-service.warehouse.svc.cluster.local:5432` | - | Database (read replica) |
| **Redis** | `redis.warehouse.svc.cluster.local:6379` | - | Кэширование |
| **Kafka** | `kafka.warehouse.svc.cluster.local:9092` | - | Messaging (KRaft) |
| **Selenoid** | `selenoid.warehouse.svc.cluster.local:4444` | `30040` | Selenium Hub |

### K8s Services (namespace: loadtest)

| Сервис | Внутренний URL | NodePort | Описание |
|--------|----------------|----------|----------|
| **Locust Master** | `locust-master-service.loadtest.svc.cluster.local:8089` | `30089` | Load testing UI |
| **Locust Workers** | - | - | 5 реплик |
| **Locust Exporter** | `locust-exporter.loadtest.svc.cluster.local:9646` | - | Prometheus метрики |

### K8s Services (namespace: notifications)

| Сервис | Внутренний URL | NodePort | Описание |
|--------|----------------|----------|----------|
| **Telegram Bot** | `gitlab-telegram-bot.notifications.svc.cluster.local:8000` | `30088` | Bot v5.4, GitLab webhooks |

### K8s Services (namespace: monitoring)

| Сервис | Внутренний URL | NodePort | Описание |
|--------|----------------|----------|----------|
| **Prometheus** | `prometheus-service.monitoring.svc.cluster.local:9090` | `30090` | Metrics |
| **Grafana** | `grafana.monitoring.svc.cluster.local:3000` | `30300` | Визуализация |
| **Alertmanager** | `alertmanager.monitoring.svc.cluster.local:9093` | - | Алертинг |

### Docker Compose сервисы (на хосте)

| Сервис | URL | Порт | Описание |
|--------|-----|------|----------|
| **GitLab CE** | http://192.168.1.74:8080 | 8080 | Git + CI/CD |
| **YouTrack** | http://192.168.1.74:8088 | 8088 | Issue tracker |
| **Allure Server** | http://192.168.1.74:5050 | 5050 | Test reports API |
| **Allure UI** | http://192.168.1.74:5252 | 5252 | Test reports UI |
| **Allure Public** | https://advertiser-dark-remaining-sail.trycloudflare.com | cloudflared | Публичный доступ |
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
  postgres:
    image: postgres:15-alpine
    ports: 5432
  nginx:
    # Reverse proxy + Let's Encrypt SSL
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

**Сценарии:**
- `receiving` — Приёмка товара
- `shipping` — Отгрузка
- `inventory` — Инвентаризация

**API Endpoints:**
- `GET /health` — Health check
- `GET /status` — Текущий статус
- `GET /stats` — Статистика
- `POST /start` — Запуск сценария
- `POST /stop` — Остановка
- `POST /schedule` — Запланировать запуск
- `GET /scheduled` — Список запланированных
- `DELETE /scheduled/{id}` — Отменить

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

**Kafka Topics:**
- `warehouse.audit` — События аудита
- `warehouse.notifications` — Уведомления о низких остатках

**API Endpoints:**
- `GET /health` — Health check
- `GET /api/stats` — Агрегированная статистика
- `GET /api/events` — Последние события
- `GET /api/hourly` — Почасовая статистика
- `GET /api/daily` — Дневная статистика
- `WS /ws` — Real-time события

**Деплой:**
```bash
cd ~/warehouse-master/analytics-service
docker build --no-cache -t analytics-service:latest .
sudo k3s ctr images rm docker.io/library/analytics-service:latest 2>/dev/null || true
docker save analytics-service:latest | sudo k3s ctr images import -
kubectl apply -k ~/warehouse-master/k8s/analytics/
```

### Telegram Bot (v5.4)

**Обновления:**
- Robot control + schedule
- PM Dashboard (YouTrack)
- Claude AI интеграция
- GitLab webhooks с WH-xxx парсингом

**Handlers:**
- `commands` — /start, /help, /status, /health, /metrics, /pods, /release
- `deploy` — Деплой staging/production
- `testing` — E2E тесты, Load testing
- `claude` — AI интеграция
- `pm` — PM Dashboard (YouTrack)
- `robot` — Robot control + schedule
- `gitlab_webhook` — GitLab webhooks

---

## Инфраструктурные сервисы

### Yandex Container Registry

```
Registry: cr.yandex/crpf5fukf1ili7kudopb
Images:
  - warehouse-api:latest
  - warehouse-frontend:latest
```

### SSH ключи

```
Путь: /home/flomaster/.ssh/
  - yc_prod_key       # Приватный ключ для деплоя на прод
  - yc_deploy_key     # Альтернативный ключ
  - id_ed25519        # Общий SSH ключ
```

---

## Учётные данные

> **ВАЖНО:** Эти данные конфиденциальны. Не коммить в публичные репозитории!

### PostgreSQL (Staging - K8s)

| Параметр | Значение |
|----------|----------|
| **Host** | `postgres-service.warehouse.svc.cluster.local` |
| **Port** | `5432` |
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
| **Project ID** | `0-1` |
| **Project Short** | `WH` |
| **User** | `admin` |
| **Password** | `Misha2021@1@` |
| **Auth** | **ТОЛЬКО Basic Auth!** |

### Deploy Passwords (Telegram Bot)

| Параметр | Значение |
|----------|----------|
| **Deploy Password** | `Misha2021@1@` |
| **Load Test Password** | `Misha2021@1@` |
| **Robot Password** | (в secrets) |
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

### Pipeline Flow

```
warehouse-api:
  validate → build → test → package
  ↓
  Docker image → Yandex Registry + K3s import

warehouse-frontend:
  build → Docker image → Yandex Registry + K3s import

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
    - run-e2e-tests
    - run-ui-tests
    - run-load-tests
```

### Артефакты (WH-155)

**Allure Projects (4 проекта):**

| Project ID | Описание | URL |
|------------|----------|-----|
| `e2e-staging` | E2E тесты на staging | http://192.168.1.74:5050/allure-docker-service/projects/e2e-staging/reports/latest |
| `e2e-prod` | E2E тесты на prod | http://192.168.1.74:5050/allure-docker-service/projects/e2e-prod/reports/latest |
| `ui-staging` | UI тесты на staging | http://192.168.1.74:5050/allure-docker-service/projects/ui-staging/reports/latest |
| `ui-prod` | UI тесты на prod | http://192.168.1.74:5050/allure-docker-service/projects/ui-prod/reports/latest |

- **Allure UI:** http://192.168.1.74:5252
- **JUnit Reports:** сохраняются в GitLab

---

## Полезные команды

### Kubernetes

```bash
# Статус всех подов
kubectl get pods -A

# Логи API
kubectl logs -n warehouse -l app=warehouse-api -f

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
```

### Docker (Staging host)

```bash
# Статус сервисов
docker ps

# Логи GitLab
docker logs gitlab -f

# Логи YouTrack
docker logs youtrack -f
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
# API
curl -s http://192.168.1.74:30080/actuator/health | jq

# Robot
curl -s http://192.168.1.74:30070/health | jq

# Analytics
curl -s http://192.168.1.74:30091/health | jq

# Frontend
curl -s http://192.168.1.74:30081/ -o /dev/null -w "%{http_code}"
```

### Нагрузочное тестирование

```bash
# Через Telegram Bot
# Кнопка "Тестирование" → "Нагрузочное тестирование"

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
| **Allure Reports** | http://192.168.1.74:5252 (внутр) / https://advertiser-dark-remaining-sail.trycloudflare.com (внешн) |
| **Locust** | http://192.168.1.74:30089 |
| **Prometheus** | http://192.168.1.74:30090 |
| **Grafana** | http://192.168.1.74:30300 |
| **Selenoid** | http://192.168.1.74:4444/wd/hub |
| **Selenoid UI** | http://192.168.1.74:8090 |
| **Orchestrator UI** | http://192.168.1.74:8000 |

---

*Последнее обновление: 2025-12-01 (WH-120 Robot, WH-121 Analytics, WH-122 Schedule, WH-155 QA v5.4)*
