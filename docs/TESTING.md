# Testing Guide

Руководство по тестированию Warehouse API и Frontend.

## Тестовые учётные записи

### API пользователи

| Username | Password | Role | Описание |
|----------|----------|------|----------|
| employee | password123 | EMPLOYEE | Сотрудник склада |
| manager | password123 | MANAGER | Менеджер |
| admin | admin123 | ADMIN | Администратор |

**ВАЖНО:** Пароль для всех тестовых пользователей — `password123` (НЕ `employee123` / `manager123`!)

### Права ролей

| Действие | EMPLOYEE | MANAGER | ADMIN |
|----------|----------|---------|-------|
| Просмотр товаров | + | + | + |
| Создание товаров | + | + | + |
| Редактирование своих товаров | + | + | + |
| Удаление своих товаров | + | + | + |
| Удаление чужих товаров | - | + | + |
| Управление пользователями | - | - | + |

---

## API Endpoints

### Base URLs

| Среда | URL |
|-------|-----|
| Staging | http://192.168.1.74:30080 |
| Production | https://api.wh-lab.ru |

### Аутентификация

```bash
# Логин
curl -X POST http://192.168.1.74:30080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "employee", "password": "password123"}'

# Ответ: {"token": "eyJhbGciOiJIUzI1NiJ9..."}

# Текущий пользователь
curl http://192.168.1.74:30080/api/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

### Продукты (Products)

```bash
# Получить все продукты
curl http://192.168.1.74:30080/api/products \
  -H "Authorization: Bearer <TOKEN>"

# Создать продукт
curl -X POST http://192.168.1.74:30080/api/products \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "quantity": 10, "price": 99.99}'

# Удалить продукт
curl -X DELETE http://192.168.1.74:30080/api/products/<ID> \
  -H "Authorization: Bearer <TOKEN>"
```

### Facilities (WH-269)

```bash
# Получить все объекты
curl http://192.168.1.74:30080/api/facilities \
  -H "Authorization: Bearer <TOKEN>"

# Получить иерархическое дерево
curl http://192.168.1.74:30080/api/facilities/tree \
  -H "Authorization: Bearer <TOKEN>"

# Создать DC (Distribution Center)
curl -X POST http://192.168.1.74:30080/api/facilities \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type": "DC", "name": "Moscow DC", "address": "Moscow, Main St"}'

# Создать WH (Warehouse)
curl -X POST http://192.168.1.74:30080/api/facilities \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type": "WH", "name": "Moscow WH #1", "parentId": 1, "address": "Moscow Region"}'

# Создать PP (Pickup Point)
curl -X POST http://192.168.1.74:30080/api/facilities \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type": "PP", "name": "Moscow PP #1-1", "parentId": 2, "address": "Moscow, Street 1"}'
```

**Коды автоматически генерируются:**
- DC → `DC-001`, `DC-002`, ...
- WH → `WH-MSK-001`, `WH-SPB-002`, ... (регион из первого WH)
- PP → `PP-MSK-001-01`, `PP-SPB-002-03`, ... (номер родителя + порядковый номер)

### Stock API (WH-270)

```bash
# Получить токен
TOKEN=$(curl -s -X POST http://192.168.1.74:30080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}' | jq -r '.token')

# Все остатки на объекте
curl -s http://192.168.1.74:30080/api/stock/facility/1 \
  -H "Authorization: Bearer $TOKEN" | jq

# Остатки товара на всех объектах
curl -s http://192.168.1.74:30080/api/stock/product/1 \
  -H "Authorization: Bearer $TOKEN" | jq

# Суммарный остаток товара
curl -s http://192.168.1.74:30080/api/stock/product/1/total \
  -H "Authorization: Bearer $TOKEN" | jq

# Конкретный остаток (товар + объект)
curl -s http://192.168.1.74:30080/api/stock/product/1/facility/1 \
  -H "Authorization: Bearer $TOKEN" | jq

# Установить остаток (100 единиц)
curl -s -X POST http://192.168.1.74:30080/api/stock/product/1/facility/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quantity":100}' | jq

# Изменить остаток (+50)
curl -s -X PATCH http://192.168.1.74:30080/api/stock/product/1/facility/1/adjust \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"delta":50}' | jq

# Зарезервировать (25 единиц)
curl -s -X POST http://192.168.1.74:30080/api/stock/product/1/facility/1/reserve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":25}' | jq

# Товары с низким остатком (threshold=10)
curl -s "http://192.168.1.74:30080/api/stock/facility/1/low?threshold=10" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Database schema (V4):**
```sql
CREATE TABLE stock (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id),
    facility_id BIGINT NOT NULL REFERENCES facilities(id),
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, facility_id),
    CHECK (quantity >= 0),
    CHECK (quantity >= reserved)
);
```

### Health Check

```bash
# Staging
curl http://192.168.1.74:30080/actuator/health

# Production
curl https://api.wh-lab.ru/actuator/health
```

---

## Frontend URLs

| Среда | URL |
|-------|-----|
| Staging | http://192.168.1.74:30081 |
| Production | https://wh-lab.ru |

### Страницы

| Путь | Описание |
|------|----------|
| `/` | Главная (редирект на /products) |
| `/login` | Страница логина |
| `/products` | Список товаров |
| `/analytics` | Аналитика (интеграция с analytics-service) |

---

## Нагрузочное тестирование

### Инструменты

| Инструмент | Назначение | UI |
|------------|------------|----|
| Locust | HTTP нагрузка на API | http://192.168.1.74:30089 |
| k6 | Kafka producer тестирование | - |

### Locust

#### Дашборды

- **Locust Web UI:** http://192.168.1.74:30089
- **Grafana Integration:** http://192.168.1.74:30300/d/integration-load-testing

#### Конфигурация

Файл: `k8s/loadtest/locust-configmap.yaml`

**StepLoadShape параметры:**

| Параметр | Значение | Описание |
|----------|----------|----------|
| step_users | 30 | Добавлять пользователей за шаг |
| step_time | 300 сек | Длительность шага (5 мин) |
| max_users | 150 | Максимум VU |
| spawn_rate | 10 | Скорость создания пользователей |

#### Типы пользователей

| Класс | Weight | Задачи |
|-------|--------|--------|
| EmployeeUser | 7 (70%) | view_products, create_product, delete_own_product, view_current_user |
| ManagerUser | 3 (30%) | view_products, view_products_detailed, view_current_user |

#### Команды

```bash
# Запуск теста со StepLoadShape
curl -X POST 'http://192.168.1.74:30089/swarm' \
  -d 'user_count=30&spawn_rate=10&shape_class=StepLoadShape'

# Остановка теста
curl -X POST 'http://192.168.1.74:30089/stop'

# Проверка статуса
curl -s 'http://192.168.1.74:30089/stats/requests' | jq '{state, user_count, total_rps, fail_ratio}'

# Сброс статистики
curl -X POST 'http://192.168.1.74:30089/stats/reset'
```

### k6 Kafka

Подробности в [LOAD_TESTING.md](LOAD_TESTING.md)

```bash
# Запуск распределённого теста (6 воркеров)
kubectl apply -f k8s/loadtest/k6/k6-testrun-distributed.yaml

# Остановка
kubectl delete testrun --all -n loadtest
```

---

## Prometheus метрики

### Locust

| Метрика | Описание |
|---------|----------|
| `locust_users` | Текущее кол-во VU |
| `locust_requests_current_rps` | Запросов в секунду |
| `locust_requests_avg_response_time` | Среднее время ответа |
| `locust_requests_num_requests` | Всего запросов |
| `locust_requests_num_failures` | Всего ошибок |
| `locust_requests_current_fail_per_sec` | Ошибок в секунду |

### Warehouse API (Spring Boot)

| Метрика | Описание |
|---------|----------|
| `http_server_requests_seconds_count` | Кол-во HTTP запросов |
| `http_server_requests_seconds_sum` | Суммарное время обработки |
| `jvm_memory_used_bytes` | Использование памяти JVM |
| `hikaricp_connections_active` | Активные DB соединения |
| `hikaricp_connections_idle` | Свободные DB соединения |

### Spring Kafka

| Метрика | Описание |
|---------|----------|
| `spring_kafka_template_seconds_count` | Кол-во отправленных сообщений |
| `spring_kafka_template_seconds_sum` | Суммарное время отправки |

---

## Очистка тестовых данных

**ОБЯЗАТЕЛЬНО выполнить ПЕРЕД запуском нагрузочного теста!**

### Kafka топики

```bash
# Найти pod Kafka
KAFKA_POD=$(kubectl get pods -n warehouse -l app=kafka -o jsonpath='{.items[0].metadata.name}')

# Очистка warehouse.audit
kubectl exec -n warehouse $KAFKA_POD -- bash -c 'cat > /tmp/delete-audit.json << EOF
{"partitions":[{"topic":"warehouse.audit","partition":0,"offset":-1},{"topic":"warehouse.audit","partition":1,"offset":-1},{"topic":"warehouse.audit","partition":2,"offset":-1}],"version":1}
EOF
/opt/kafka/bin/kafka-delete-records.sh --bootstrap-server localhost:9092 --offset-json-file /tmp/delete-audit.json'

# Очистка warehouse.notifications
kubectl exec -n warehouse $KAFKA_POD -- bash -c 'cat > /tmp/delete-notifications.json << EOF
{"partitions":[{"topic":"warehouse.notifications","partition":0,"offset":-1},{"topic":"warehouse.notifications","partition":1,"offset":-1},{"topic":"warehouse.notifications","partition":2,"offset":-1}],"version":1}
EOF
/opt/kafka/bin/kafka-delete-records.sh --bootstrap-server localhost:9092 --offset-json-file /tmp/delete-notifications.json'
```

### Redis (аналитика)

```bash
# Найти pod Redis
REDIS_POD=$(kubectl get pods -n warehouse -l app=redis -o jsonpath='{.items[0].metadata.name}')

# Очистить DB 1 (analytics-service)
kubectl exec -n warehouse $REDIS_POD -- redis-cli -n 1 FLUSHDB
```

---

## Troubleshooting

### Locust: 100% ошибок на логине

**Причина:** Неправильные пароли в locustfile

**Решение:**
1. Проверить `k8s/loadtest/locust-configmap.yaml`
2. Убедиться что пароль = `password123`
3. Применить configmap: `kubectl apply -f k8s/loadtest/locust-configmap.yaml`
4. Перезапустить Locust: `kubectl rollout restart deployment/locust-master deployment/locust-worker -n loadtest`

### Kafka метрики пустые на дашборде

**Причина:** Используются k6 метрики, а k6 не запущен

**Решение:** Использовать Spring Kafka метрики:
- `spring_kafka_template_seconds_count` вместо `k6_kafka_messages_produced_total_total`

### Grafana: No data

1. Проверить datasource UID: `PBFA97CFB590B2093`
2. Проверить что метрики есть в Prometheus:
   ```bash
   curl -s "http://192.168.1.74:30090/api/v1/query?query=locust_users"
   ```
