# Backlog: Оптимизация проекта

## Приоритет 1: Критично

### OPT-001: Безопасность — вынести секреты из кода
**Labels:** security, critical
**Описание:** JWT_SECRET и другие секреты захардкожены в docker-compose.yml и конфигах.

**Задачи:**
- [ ] Вынести все секреты в .env файлы
- [ ] Добавить .env.example как шаблон
- [ ] Настроить K8s Secrets для всех credentials
- [ ] Добавить Redis password (сейчас без пароля)
- [ ] Убедиться что .env в .gitignore

---

### OPT-002: API — добавить пагинацию
**Labels:** enhancement, api
**Описание:** Endpoints возвращают все записи без пагинации — проблема при большом объёме данных.

**Задачи:**
- [ ] Добавить Page/Pageable в контроллеры (products, stock, documents)
- [ ] Фронтенд: добавить infinite scroll или pagination
- [ ] Добавить лимиты по умолчанию (page=0, size=20)

---

### OPT-003: Тесты — покрытие unit тестами
**Labels:** testing, quality
**Описание:** Есть E2E тесты, но мало unit тестов для сервисов.

**Задачи:**
- [ ] Unit tests для ReceiptService (edge cases)
- [ ] Unit tests для ShipmentService (stock validation)
- [ ] Unit tests для IssueActService
- [ ] Unit tests для InventoryActService
- [ ] Настроить JaCoCo для coverage report

---

## Приоритет 2: Важно

### OPT-004: Frontend — оптимизация bundle
**Labels:** frontend, performance
**Описание:** Bundle size можно уменьшить.

**Задачи:**
- [ ] Lazy loading для routes (dc/, wh/, pp/)
- [ ] Code splitting для document components
- [ ] Проверить tree-shaking
- [ ] Добавить compression (gzip/brotli)

---

### OPT-005: API — кэширование с Redis
**Labels:** api, performance
**Описание:** Redis подключен, но не используется для кэширования.

**Задачи:**
- [ ] Кэшировать GET /facilities (редко меняется)
- [ ] Кэшировать GET /products (с invalidation при изменении)
- [ ] Кэшировать GET /stock/{facilityId} (TTL 30s)
- [ ] Добавить @Cacheable аннотации

---

### OPT-006: Kafka — retry и dead letter queue
**Labels:** kafka, reliability
**Описание:** При ошибке обработки сообщение теряется.

**Задачи:**
- [ ] Настроить retry policy (3 attempts)
- [ ] Добавить dead letter topic
- [ ] Логирование failed messages
- [ ] Alert при накоплении в DLQ

---

### OPT-007: CI/CD — автоматические тесты
**Labels:** ci-cd, testing
**Описание:** Тесты запускаются вручную.

**Задачи:**
- [ ] Автозапуск unit tests на каждый push
- [ ] E2E тесты на develop branch
- [ ] Блокировка merge при failed tests
- [ ] Coverage threshold (минимум 70%)

---

## Приоритет 3: Улучшения

### OPT-008: Документация — OpenAPI/Swagger
**Labels:** docs, api
**Описание:** Нет интерактивной документации API.

**Задачи:**
- [ ] Добавить springdoc-openapi
- [ ] Настроить Swagger UI
- [ ] Добавить описания к endpoints
- [ ] Примеры request/response

---

### OPT-009: Мониторинг — бизнес метрики
**Labels:** monitoring, observability
**Описание:** Есть технические метрики, нет бизнес метрик.

**Задачи:**
- [ ] Метрика: документов создано/день
- [ ] Метрика: среднее время обработки документа
- [ ] Метрика: товаров в движении
- [ ] Grafana dashboard для бизнеса

---

### OPT-010: Frontend — PWA support
**Labels:** frontend, enhancement
**Описание:** Добавить offline возможности для PP.

**Задачи:**
- [ ] Service Worker
- [ ] Offline cache для справочников
- [ ] Push notifications
- [ ] Install prompt

---

### OPT-011: API — rate limiting
**Labels:** api, security
**Описание:** Защита от DDoS и abuse.

**Задачи:**
- [ ] Rate limiting на auth endpoints (10 req/min)
- [ ] Rate limiting на API (100 req/min per user)
- [ ] Добавить X-RateLimit-* headers
- [ ] Bucket4j или Spring Cloud Gateway

---

### OPT-012: Database — индексы и оптимизация
**Labels:** database, performance
**Описание:** Проверить и оптимизировать запросы.

**Задачи:**
- [ ] Добавить индексы на foreign keys
- [ ] Индекс на stock(facility_id, product_id)
- [ ] Индекс на documents(status, created_at)
- [ ] Анализ slow queries
- [ ] EXPLAIN для тяжёлых запросов

---

## Приоритет 4: Nice to have

### OPT-013: Audit log
**Labels:** feature, security
**Описание:** История изменений для compliance.

**Задачи:**
- [ ] Таблица audit_log
- [ ] Логирование CREATE/UPDATE/DELETE
- [ ] Хранение old_value/new_value
- [ ] UI для просмотра истории

---

### OPT-014: Bulk operations
**Labels:** feature, api
**Описание:** Массовые операции для эффективности.

**Задачи:**
- [ ] Bulk create products (CSV import)
- [ ] Bulk update stock
- [ ] Batch processing для документов
- [ ] Progress indicator на фронте

---

### OPT-015: Reports — экспорт
**Labels:** feature, reports
**Описание:** Экспорт данных в Excel/PDF.

**Задачи:**
- [ ] Export stock to Excel
- [ ] Export documents to PDF
- [ ] Scheduled reports по email
- [ ] Report templates

---

## Технический долг

### TECH-001: Очистка deprecated кода
- [ ] Убрать неиспользуемые endpoints
- [ ] Убрать закомментированный код
- [ ] Удалить unused dependencies

### TECH-002: Обновление зависимостей
- [ ] Spring Boot 3.2 → 3.3
- [ ] Vue.js security updates
- [ ] npm audit fix

### TECH-003: Docker images optimization
- [ ] Multi-stage builds (уже есть, проверить)
- [ ] Alpine base images
- [ ] Layer caching optimization
- [ ] Image size audit

---

## Создание GitHub Issues

```bash
# После установки gh CLI выполнить:

# OPT-001
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "OPT-001: Безопасность — вынести секреты из кода" \
  --label "security,critical" \
  --body "JWT_SECRET и другие секреты захардкожены. Вынести в .env и K8s Secrets."

# OPT-002
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "OPT-002: API — добавить пагинацию" \
  --label "enhancement,api" \
  --body "Endpoints возвращают все записи. Добавить Page/Pageable."

# ... и т.д.
```
