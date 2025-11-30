# WH-112: Test C - Optimized + Scaling Report

**Дата:** 2025-11-30
**Режим:** OPTIMIZED + SCALING (2 реплики API, увеличенные ресурсы)
**Цель:** http://warehouse-api-service.warehouse.svc.cluster.local:8080
**Остановка:** Error threshold reached (5.250754147812971%)

## Конфигурация Test C

| Параметр | Значение |
|----------|----------|
| API Replicas | 2 |
| API CPU Limit | 1000m |
| API Memory Limit | 1Gi |
| Rate Limiting | OFF |
| Redis maxclients | 10000 |
| Locust Workers | 8 |

## Результаты

### Ключевые метрики
| Метрика | Значение |
|---------|----------|
| Max Users достигнуто | 500 |
| Max RPS | 55.0 |
| Final Error Rate | 5% |
| Total Requests | 84874 |
| Total Failures | 4456 |
| Avg Latency | 7160ms |

### Статистика по эндпоинтам

| Endpoint | Requests | Failures | Fail% | Avg (ms) |
|----------|----------|----------|-------|----------|
| /api/auth/login | 548 | 35 | 6% | 20745 |
| /api/auth/me | 8935 | 458 | 5% | 7290 |
| /api/products (GET) | 44440 | 2219 | 4% | 6868 |
| /api/products (POST) | 11606 | 666 | 5% | 7499 |
| /api/products/[id] (DELETE) | 523 | 34 | 6% | 7873 |
| /api/products/[id] (PUT) | 1046 | 45 | 4% | 7457 |
| /api/products/[id] (cleanup) | 56 | 0 | 0% | 522 |
| /api/products?category (GET) | 17720 | 999 | 5% | 7165 |
| **TOTAL** | 84874 | 4456 | 5% | 7160 |

## Сравнение A/B/C

| Метрика | Test A (Baseline) | Test B (Optimized) | Test C (Scaling) |
|---------|-------------------|--------------------|--------------------|
| Max Users (до 3% err) | ~200-300 | ~150-200 | **500** |
| Max RPS | ~19 | ~16 | **55.0** |
| Конфигурация | 1 replica, no cache | 1 replica, Redis+Kafka | 2 replicas, optimized |

## Рекомендации для Test D

### Вариант 1: Дополнительное горизонтальное масштабирование
```bash
kubectl scale deployment/warehouse-api -n warehouse --replicas=4
kubectl scale deployment/locust-worker -n loadtest --replicas=12
```
**Ожидание:** +50-100% throughput

### Вариант 2: Оптимизация PostgreSQL
```bash
# Увеличить connection pool
kubectl set env deployment/warehouse-api -n warehouse \
  SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE=20
# Добавить реплику PostgreSQL (read replica)
```
**Ожидание:** Снижение latency на READ операциях

### Вариант 3: Оптимизация BCrypt
```java
// В коде: снизить cost factor с 12 до 10
BCryptPasswordEncoder(10) // вместо 12
```
**Ожидание:** ~4x ускорение логина (но снижение безопасности)

### Вариант 4: JWT Token Caching
```java
// Кэширование валидации JWT в Redis
@Cacheable("jwt-validation")
public boolean validateToken(String token) { ... }
```
**Ожидание:** Снижение CPU на повторных запросах

### Рекомендуемый порядок для Test D:
1. **Вариант 1** - горизонтальное масштабирование (без изменения кода)
2. **Вариант 2** - если DB станет bottleneck

---
*Отчёт создан автоматически: Sun Nov 30 02:08:04 UTC 2025*
*Задача: WH-112*
