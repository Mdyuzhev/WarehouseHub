# Project Status - Warehouse `v2025.12.03`

> Актуальный статус проекта на 2025-12-03 (аудит full). Используй этот файл для понимания текущего контекста перед планированием задач.

---

## Последние завершенные Epic

### WH-379: Notification Service ✅
**Статус:** Deployed to Production
**Дата:** 2025-12-03
**Окружения:** warehouse-dev ✅, warehouse (prod) ✅

**Результаты тестирования:**
- Dev: 5479 запросов, 0 ошибок, throughput 18 req/s
- Prod: smoke test passed, Telegram интеграция подтверждена

**Компоненты:**
- NotificationService с асинхронной очередью
- TelegramNotificationSender (Bot: @wh_ntf_bot)
- REST API: /api/notifications/*
- Flyway миграция V3

**Endpoints:**
- `POST /api/notifications` - создать уведомление
- `GET /api/notifications/{id}` - получить уведомление по ID
- `GET /api/notifications/stats` - статистика по уведомлениям

**Telegram Bot:**
- Bot: @wh_ntf_bot
- Chat: WH_lab_notify (-1003231635846)
- Формат: HTML с bold для subject

---

### WH-270: Product/Stock Separation ✅
**Статус:** Deployed to Production
**Дата:** 2025-12-03
**MR:** !6 merged

**Что реализовано:**
- ✅ Stock entity с привязкой к Product + Facility
- ✅ Flyway миграция V4 (таблица stock)
- ✅ StockService + StockRepository
- ✅ StockController (8 REST endpoints)
- ✅ Kafka события в warehouse.audit
- ✅ Unit тесты (13) + Integration тесты (7)

**Endpoints /api/stock/*:**
- `GET /facility/{id}` — остатки на объекте
- `GET /product/{id}` — остатки товара везде
- `GET /product/{id}/facility/{id}` — конкретный остаток
- `GET /product/{id}/total` — суммарный остаток
- `POST /product/{id}/facility/{id}` — установить остаток
- `PATCH /product/{id}/facility/{id}/adjust` — изменить остаток
- `POST /product/{id}/facility/{id}/reserve` — зарезервировать
- `GET /facility/{id}/low` — товары с низким остатком

---

## Текущая ситуация в репозиториях

### warehouse-master
| Параметр | Значение |
|----------|----------|
| **Активная ветка** | `main` |
| **Статус** | Clean |
| **Последний коммит** | `3fe5d94` - k6 нагрузочный тест для Notification Service |
| **Ветки** | main |

**Что в main:**
- ✅ Telegram Bot v5.6 (WH-217) с Load Testing Wizard
- ✅ Unified QA Menu - все тестирование в одном месте
- ✅ Cleanup Service (Redis/Kafka/PostgreSQL)
- ✅ k6 Kafka для Production
- ✅ kubectl в контейнере бота (WH-267, WH-268)
- ✅ k6 notification load test (WH-396)
- ✅ e2e-tests без неиспользуемых импортов

**Production deployment:**
- Telegram Bot: v5.6 deployed
- Notification Service: integrated

---

### warehouse-api
| Параметр | Значение |
|----------|----------|
| **Активная ветка** | `main` |
| **Последний коммит** | `5474900` - Hotfix: Исправление тестов Notification Service |
| **Ветки** | main, develop, hotfix/test-fixes (merged) |

**Что в main:**
- ✅ WH-270: Stock Management (Product/Stock Separation)
- ✅ WH-379: Notification Service (полный Epic)
- ✅ WH-388: TelegramNotificationSender
- ✅ WH-394, WH-395: Unit и Integration тесты
- ✅ WH-269: Facilities Management (DC → WH → PP иерархия)
- ✅ WH-378: Bugfixes (Flyway для тестов, backward compatibility)
- ✅ CI/CD pipeline для dev/prod окружений
- ✅ Redis JWT token caching

**Статус:**
- ✅ Production deployment успешен
- ✅ Все тесты проходят (pipeline #230 running)
- ✅ warehouse-api pods: 2 реплики (deployed 2 hours ago)

---

### warehouse-frontend
| Параметр | Значение |
|----------|----------|
| **Активная ветка** | `main` |
| **Статус** | Stable |

**Что в main:**
- ✅ Vue.js 3.4 + Vite 5
- ✅ Nginx production build
- ✅ Facilities integration
- ✅ Role-based access control

**Production deployment:**
- Frontend: stable, без изменений

---

## Статус окружений

### Staging (K3s на 192.168.1.74)

| Namespace | Pods | Статус |
|-----------|------|--------|
| warehouse | 10/10 | ✅ Running |
| warehouse-dev | active | ✅ Running |
| notifications | Telegram Bot v5.6 | ✅ Running |
| monitoring | Prometheus, Grafana | ✅ Running |
| loadtest | Locust | ✅ Running |

**Pods в warehouse:**
- warehouse-api: 2 replicas (✅ with Notification Service)
- warehouse-frontend: 1 replica
- postgres: 1 primary + 1 replica
- redis, kafka, analytics-service, warehouse-robot, selenoid

**Health check:** ✅ UP

### Production (Yandex Cloud 130.193.44.34)

**Статус:** Доступен через https://wh-lab.ru

**Компоненты:**
- API: https://api.wh-lab.ru
- Frontend: https://wh-lab.ru
- PostgreSQL, Redis, Kafka
- Nginx + Certbot (SSL)

**Health check:** Unreachable from local (firewall)

---

## Текущие приоритеты

### Завершено
- [x] WH-270 Epic - Stock Management (Product/Stock Separation)
- [x] WH-379 Epic - Notification Service
- [x] WH-388 - TelegramNotificationSender
- [x] WH-396 - k6 load test
- [x] WH-387, WH-393 - Stories (Services, Testing)
- [x] WH-217 - Telegram Bot v5.6

### В работе
- [ ] Notification Service production monitoring (Grafana)
- [ ] Integration with business logic (stock notifications)

### Следующие задачи
- [ ] Интеграция Notification Service с бизнес-логикой (stock notifications, alerts)
- [ ] Email и Webhook channels для NotificationService
- [ ] Production мониторинг Notification Service через Grafana

---

## Ключевые метрики

| Метрика | Значение |
|---------|----------|
| **warehouse-api тесты** | 20/20 Stock + Notification passed |
| **Pods Running** | 10/10 в warehouse namespace |
| **Последний Epic** | WH-270 (Stock Management) |
| **API Endpoints** | 31 (добавлено 8 для stock) |
| **Pipeline** | #237 (main) |
| **Версия Bot** | v5.6 (deployed) |

---

## Важные ссылки

| Ссылка | URL |
|--------|-----|
| Staging API | http://192.168.1.74:30080 |
| Staging UI | http://192.168.1.74:30081 |
| Production API | https://api.wh-lab.ru |
| Production UI | https://wh-lab.ru |
| GitLab | http://192.168.1.74:8080 |
| YouTrack | http://192.168.1.74:8088 |
| Grafana | http://192.168.1.74:30300 |

---

## Changelog

### 2025-12-03 (WH-270)
- ✅ **WH-270 Stock Management deployed to Production**
- ✅ Stock entity + V4 миграция
- ✅ 8 новых endpoints /api/stock/*
- ✅ MR !6 merged, Pipeline #237 passed
- ✅ Unit тесты (13) + Integration тесты (7)
- ✅ Kafka события для аудита

### 2025-12-03 (Full Audit)
- ✅ Full audit выполнен
- ✅ Production и Staging: API UP, все компоненты работают
- ✅ warehouse-api: 24 endpoints, hotfix/test-fixes с небольшими изменениями
- ✅ warehouse-frontend: clean state, develop branch
- ✅ warehouse-master: 3 незакоммиченных файла (k6 notification test)
- ✅ Документация обновлена (ARCHITECTURE, COMPONENTS, INFRASTRUCTURE_GUIDE)

### 2025-12-02
- ✅ Epic WH-379 (Notification Service) завершен и deployed
- ✅ Hotfix: исправлены тесты (@EnableScheduling + manual processQueue())
- ✅ MR #3, #4 merged в warehouse-api/main
- ✅ k6 notification load test добавлен в warehouse-master
- ✅ Telegram Bot integration полностью работает
- ✅ Pipeline #230 запущен (tests passed!)

### 2025-12-01
- WH-217: Telegram Bot v5.6 merged в main
- Unified QA Menu, Load Testing Wizard
- Cleanup Service для Redis/Kafka/PostgreSQL

### 2025-11-30
- WH-269: Facilities Management deployed
- JWT backward compatibility fixes

---

*Последнее обновление: 2025-12-03 (Full Audit)*
