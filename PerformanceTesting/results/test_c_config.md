# WH-112: Test C - Конфигурационные оптимизации

**Дата:** 2025-11-30
**Режим:** OPTIMIZED + SCALING (без изменения кода)
**Цель:** Максимальная производительность через настройки K8s

## Применённые оптимизации

### 1. Горизонтальное масштабирование API

```bash
kubectl scale deployment/warehouse-api -n warehouse --replicas=2
```

| Параметр | До | После |
|----------|-----|-------|
| Replicas | 1 | **2** |

**Цель:** Распределить CPU-нагрузку BCrypt между подами.

### 2. Увеличение ресурсов API

```bash
kubectl set resources deployment/warehouse-api -n warehouse \
  --limits=cpu=1000m,memory=1Gi \
  --requests=cpu=500m,memory=512Mi
```

| Параметр | До | После |
|----------|-----|-------|
| CPU requests | 250m | **500m** |
| CPU limits | 500m | **1000m** |
| Memory requests | 256Mi | **512Mi** |
| Memory limits | 512Mi | **1Gi** |

**Цель:** Дать больше CPU для BCrypt-операций.

### 3. Отключение Rate Limiting

```bash
kubectl set env deployment/warehouse-api -n warehouse RATE_LIMIT_ENABLED=false
```

| Параметр | До | После |
|----------|-----|-------|
| RATE_LIMIT_ENABLED | true | **false** |

**Цель:** Убрать искусственные ограничения (429 ошибки) для чистого теста производительности.

### 4. Оптимизация Redis

```bash
kubectl exec -n warehouse deployment/redis -- redis-cli CONFIG SET maxclients 10000
kubectl exec -n warehouse deployment/redis -- redis-cli FLUSHALL
```

| Параметр | До | После |
|----------|-----|-------|
| maxclients | 1000 (default) | **10000** |
| Cached data | ~50MB | **0** (очищено) |

**Цель:** Предотвратить ошибки "too many clients" при высокой нагрузке.

### 5. Масштабирование Locust

```bash
kubectl scale deployment/locust-worker -n loadtest --replicas=8
```

| Параметр | До | После |
|----------|-----|-------|
| Workers | 5 | **8** |
| Max users per worker | ~40 | ~40 |
| Total capacity | ~200 | **~320** |

**Цель:** Увеличить генерируемую нагрузку для выявления реального потолка системы.

## Сводная таблица изменений

| Компонент | Изменение | Ожидаемый эффект |
|-----------|-----------|------------------|
| warehouse-api replicas | 1 → 2 | +100% throughput на BCrypt |
| warehouse-api CPU | 500m → 1000m | Быстрее хэширование паролей |
| warehouse-api Memory | 512Mi → 1Gi | Больше connection pool |
| Rate limiting | ON → OFF | Нет 429 ошибок |
| Redis maxclients | 1000 → 10000 | Нет ошибок подключения |
| Locust workers | 5 → 8 | Больше concurrent users |

## Ограничения (НЕ менялось)

❌ **Код не изменялся:**
- BCrypt cost factor остался 12
- JWT TTL остался стандартным
- Connection pool sizes не менялись в коде
- Никаких изменений в `warehouse-api` source code

❌ **Инфраструктура не менялась:**
- PostgreSQL: 1 replica, стандартные limits
- Redis: 1 replica, только maxclients
- Kafka: 1 replica
- Node resources: без изменений

## Baseline для сравнения

| Тест | API Replicas | CPU Limit | Rate Limit | Max Users |
|------|--------------|-----------|------------|-----------|
| A (Baseline) | 1 | 500m | ON | ~200-300 |
| B (Optimized) | 1 | 500m | ON | ~150-200 |
| C (Scaling) | **2** | **1000m** | **OFF** | TBD |

## Мониторинг

Начальные показатели Test C (10 users):
- RPS: 7 (vs 5 в Test B)
- Errors: 0%
- Avg latency: 868ms

---
*Документ создан: 2025-11-30*
*Задача: WH-112*
