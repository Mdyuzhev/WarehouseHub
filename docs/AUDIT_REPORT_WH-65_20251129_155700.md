# Аудит-отчёт: WH-65 Инфраструктурные улучшения

**Дата:** 29 ноября 2025
**Версия:** 1.0
**Задача:** [WH-65](http://192.168.1.74:8088/issue/WH-65)

---

## Краткое резюме

В рамках WH-65 была проведена масштабная работа по улучшению инфраструктуры проекта Warehouse. Добавлены:
- **Redis** — кэширование данных и rate limiting
- **Kafka KRaft** — аудит действий и уведомления о низком стоке
- **Selenoid** — инфраструктура для UI-тестов
- **Grafana** — визуализация метрик
- **Telegram Bot** — исправление ошибок и структурированное логирование

---

## 1. Redis — Кэширование и защита

### Что добавлено

| Компонент | Файл | Назначение |
|-----------|------|------------|
| K8s Deployment | `k8s/warehouse/redis-deployment.yaml` | Redis 7-alpine, 256Mi RAM |
| K8s Service | `k8s/warehouse/redis-service.yaml` | ClusterIP :6379 |
| K8s ConfigMap | `k8s/warehouse/redis-configmap.yaml` | maxmemory 200mb, allkeys-lru |
| Java Config | `RedisConfig.java` | Spring Cache с TTL 5 мин |
| Rate Limiting | `RateLimitingService.java` | 5 попыток / 15 минут |
| Token Blacklist | `TokenBlacklistService.java` | Инвалидация JWT при logout |

### Как увидеть что работает

**1. Rate Limiting в действии:**
```bash
# После 5 неудачных попыток логина:
curl -X POST http://192.168.1.74:30080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"wrong"}'

# Ответ после 6-й попытки:
{"error": "Too many login attempts. Please try again later."}
```

**2. Redis ключи:**
```bash
kubectl exec -it redis-xxx -n warehouse -- redis-cli KEYS "*"
# Результат: rate_limit:login:username:ip
```

**3. Health endpoint:**
```bash
curl http://192.168.1.74:30080/actuator/health | jq '.components.redis'
# {"status":"UP","details":{"version":"7.4.7"}}
```

### Где в коде

- `ProductService.java:62-72` — `@Cacheable` для списка продуктов
- `ProductService.java:44-60` — `@CacheEvict` при создании/обновлении
- `AuthController.java:45-55` — проверка rate limit перед логином
- `JwtAuthenticationFilter.java:40-50` — проверка blacklist токенов

---

## 2. Kafka KRaft — Аудит и уведомления

### Что добавлено

| Компонент | Файл | Назначение |
|-----------|------|------------|
| K8s Deployment | `k8s/warehouse/kafka-deployment.yaml` | Apache Kafka 3.7.0 (KRaft) |
| K8s Service | `k8s/warehouse/kafka-service.yaml` | ClusterIP :9092 |
| K8s ConfigMap | `k8s/warehouse/kafka-configmap.yaml` | cluster-id |
| Java Config | `KafkaConfig.java` | Топики audit/notifications |
| Audit Service | `AuditService.java` | Логирование CRUD операций |
| Stock Notify | `StockNotificationService.java` | LOW_STOCK, OUT_OF_STOCK |

### Топики Kafka

```bash
kubectl exec -it kafka-xxx -n warehouse -- \
  /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Результат:
# warehouse.audit
# warehouse.notifications
```

### События аудита

| Событие | Когда срабатывает |
|---------|-------------------|
| `LOGIN` | Успешный вход пользователя |
| `LOGOUT` | Выход (инвалидация токена) |
| `CREATE` | Создание продукта |
| `UPDATE` | Обновление продукта |
| `DELETE` | Удаление продукта |

### Уведомления о стоке

| Уведомление | Условие |
|-------------|---------|
| `LOW_STOCK` | quantity <= 10 (настраивается) |
| `OUT_OF_STOCK` | quantity = 0 |

### Где в коде

- `ProductService.java:51-57` — отправка audit и stock events
- `AuditService.java:30-45` — формирование AuditEvent
- `StockNotificationService.java:25-40` — проверка порогов стока

---

## 3. Selenoid — UI тестирование

### Что добавлено

| Компонент | Файл | Назначение |
|-----------|------|------------|
| K8s Deployment | `k8s/warehouse/selenoid-deployment.yaml` | Selenoid с browsers.json |
| K8s Service | `k8s/warehouse/selenoid-service.yaml` | ClusterIP :4444 |
| K8s ConfigMap | `k8s/warehouse/selenoid-configmap.yaml` | Chrome/Firefox конфиг |

### UI тесты (новый модуль)

```
ui-tests/
├── pom.xml                           # Selenide 7.0.4, JUnit 5, Allure
└── src/test/java/com/warehouse/ui/
    ├── config/
    │   ├── BaseTest.java             # Selenoid remote WebDriver
    │   └── TestConfig.java           # Конфигурация
    ├── pages/
    │   ├── LoginPage.java            # Page Object: логин
    │   └── ProductsPage.java         # Page Object: продукты
    └── tests/
        ├── LoginTest.java            # Тесты логина
        ├── ProductsTest.java         # Тесты CRUD продуктов
        └── RoleAccessTest.java       # Тесты доступа по ролям
```

### Как запустить тесты

```bash
cd ui-tests
mvn clean test -Dselenide.remote=http://selenoid:4444/wd/hub
```

### CI интеграция

В `.gitlab-ci.yml` добавлен job:
```yaml
run-ui-tests:
  stage: test
  script:
    - cd ui-tests && mvn clean test
  artifacts:
    paths:
      - ui-tests/target/allure-results
```

---

## 4. Grafana — Мониторинг

### Что добавлено

| Компонент | Файл | Назначение |
|-----------|------|------------|
| K8s Deployment | `k8s/monitoring/grafana-deployment.yaml` | Grafana 10.2.2 |
| K8s Service | `k8s/monitoring/grafana-service.yaml` | NodePort :30300 |
| K8s Secret | `k8s/monitoring/grafana-secret.yaml` | admin password |
| Datasources | `k8s/monitoring/grafana-datasources.yaml` | Prometheus |
| Dashboard | `k8s/monitoring/grafana-dashboards.yaml` | Warehouse API |

### Доступ

| URL | Credentials |
|-----|-------------|
| http://192.168.1.74:30300 | admin / warehouse2025 |

### Dashboard "Warehouse API"

| Панель | Метрика | Описание |
|--------|---------|----------|
| API Request Rate | `rate(http_server_requests_seconds_count)` | Запросов/сек |
| Response Time p95 | `histogram_quantile(0.95, ...)` | 95-й перцентиль |
| Error Rate | `rate(...{status=~"4..\|5.."})` | Ошибки 4xx/5xx |
| JVM Memory | `jvm_memory_used_bytes` | Использование heap |
| Products Created | `warehouse_products_created_total` | Бизнес-метрика |
| Products Deleted | `warehouse_products_deleted_total` | Бизнес-метрика |
| DB Connections | `hikaricp_connections_active` | Пул соединений |

### Prometheus метрики

```bash
curl http://192.168.1.74:30080/actuator/prometheus | grep warehouse
# warehouse_products_created_total{...} 0.0
# warehouse_products_deleted_total{...} 0.0
```

---

## 5. Telegram Bot — Улучшения

### Исправление 409 Conflict

**Проблема:** При RollingUpdate два пода бота конфликтовали за getUpdates.

**Решение:**
- `strategy: Recreate` в deployment
- Graceful shutdown с signal handlers (SIGTERM/SIGINT)
- `terminationGracePeriodSeconds: 15`
- Exponential backoff при ошибках

### Структурированное логирование

```python
# JSON формат для K8s (Loki/ELK/Fluentd)
{
  "timestamp": "2025-11-29T15:00:00.000Z",
  "level": "INFO",
  "logger": "app",
  "message": "Pipeline completed",
  "service": "gitlab-telegram-bot",
  "version": "1.0.0"
}
```

### Файлы изменены

- `telegram-bot/app.py` — shutdown handlers, backoff
- `telegram-bot/bot/telegram.py` — улучшенная обработка 409
- `telegram-bot/config.py` — LOG_FORMAT, LOG_LEVEL
- `k8s/notifications/bot-deployment.yaml` — Recreate strategy

---

## 6. Технические решения

### Опциональность сервисов

Все новые сервисы сделаны опциональными для работы без Redis/Kafka:

```java
// Условная загрузка конфигурации
@ConditionalOnProperty(name = "spring.cache.type", havingValue = "redis")
public class RedisConfig { ... }

// Опциональная инъекция
@Autowired(required = false)
private RateLimitingService rateLimitingService;

// Проверка перед использованием
if (auditService != null) {
    auditService.logProductCreate(...);
}
```

### K8s environment variable conflict

**Проблема:** K8s создаёт `REDIS_PORT=tcp://IP:port` что ломает `spring.data.redis.port`.

**Решение:** Захардкожены значения в `application-k8s.properties`:
```properties
spring.data.redis.host=redis
spring.data.redis.port=6379
```

---

## 7. Коммиты

### warehouse-api
| SHA | Сообщение |
|-----|-----------|
| `d094910` | feat(WH-65): Add Redis caching, Kafka audit, rate limiting |
| `be38253` | fix: Make Redis/Kafka services optional for tests |
| `bb1c16a` | fix: Make Kafka services fully optional for tests |
| `98e050b` | fix: Make RedisConfig conditional on spring.cache.type=redis |
| `06684bb` | fix: Hardcode Redis host/port to avoid K8s env var conflict |
| `70237b4` | fix: Add Serializable to Product for Redis caching |

### warehouse-master
| SHA | Сообщение |
|-----|-----------|
| `f64660e` | feat(WH-65): Infrastructure improvements |
| `c80c5d2` | fix: Update Kafka image and Grafana port |

---

## 8. Проверка работоспособности

### Быстрая проверка всех сервисов

```bash
# API Health (Redis + DB)
curl http://192.168.1.74:30080/actuator/health | jq '.status, .components.redis.status, .components.db.status'
# UP UP UP

# Grafana
curl http://192.168.1.74:30300/api/health | jq '.database'
# ok

# Kafka топики
kubectl exec -it kafka-xxx -n warehouse -- /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
# warehouse.audit
# warehouse.notifications

# Rate Limiting
# 6 попыток логина с неверным паролем → блокировка

# Redis ключи
kubectl exec -it redis-xxx -n warehouse -- redis-cli KEYS "*"
# rate_limit:login:...
```

---

## 9. Доступы

| Сервис | URL | Credentials |
|--------|-----|-------------|
| Frontend | http://192.168.1.74:30000 | - |
| API | http://192.168.1.74:30080 | JWT |
| Swagger | http://192.168.1.74:30080/swagger-ui.html | - |
| Grafana | http://192.168.1.74:30300 | admin / warehouse2025 |
| Prometheus | http://192.168.1.74:30090 | - |

---

## 10. Что изменилось визуально

### До WH-65
- API без кэширования (каждый запрос → БД)
- Нет защиты от brute-force
- Нет аудита действий
- Нет мониторинга метрик
- Telegram бот падал с 409 при деплое

### После WH-65

1. **API быстрее** — продукты кэшируются в Redis (TTL 5 мин)
2. **Защита от brute-force** — 5 попыток логина, потом блокировка 15 мин
3. **Аудит в Kafka** — все CRUD операции логируются
4. **Grafana dashboard** — визуализация метрик в реальном времени
5. **UI тесты готовы** — Selenoid + Selenide модуль
6. **Telegram бот стабилен** — graceful shutdown, без 409

### Где посмотреть

| Что | Где увидеть |
|-----|-------------|
| Redis кэш | `redis-cli KEYS "*"` |
| Rate limit | 6 неудачных логинов → блокировка |
| Kafka events | `kafka-console-consumer --topic warehouse.audit` |
| Метрики | http://192.168.1.74:30300 (Grafana) |
| Bot логи | `kubectl logs gitlab-telegram-bot-xxx -n notifications` |

---

*Отчёт создан Claude Code*
*29 ноября 2025*
