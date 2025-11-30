# Сравнительный отчёт нагрузочных тестов A/B/C/D

**Последнее обновление:** 2025-11-30
**Задачи:** WH-109, WH-110, WH-112, WH-113

---

## Краткая сводка

| Тест | Конфигурация | Max Users | Max RPS | Результат |
|------|--------------|-----------|---------|-----------|
| **A (Baseline)** | 1 replica, no cache | ~200-300 | ~19 | Baseline |
| **B (Optimized)** | 1 replica, Redis+Kafka | ~150-200 | ~16 | +Redis не помог BCrypt |
| **C (Scaling)** | 2 replicas, optimized | **500** | **55** | **+150% users, +244% RPS** |
| **D (Extended)** | 4 replicas, 12 workers | ~150-200 | **71.7** | DB connections bottleneck |

---

## Test A: Baseline (WH-109)

**Дата:** 2025-11-30
**Конфигурация:**
- API Replicas: 1
- Redis: OFF (SPRING_CACHE_TYPE=none)
- Kafka: OFF
- Rate Limiting: ON
- Locust Workers: 5

### Результаты
| Метрика | Значение |
|---------|----------|
| Max Users до 5% ошибок | ~200-300 |
| Max Users при отказе | 400 |
| Max RPS | ~19 |
| Final Error Rate | 59% |
| Total Requests | 26,297 |
| Avg Latency при отказе | 15,156ms |

### Bottleneck
- **/api/auth/login: 98% ошибок** - BCrypt CPU-bound
- GET операции: 40% ошибок

---

## Test B: Optimized (WH-110)

**Дата:** 2025-11-30
**Конфигурация:**
- API Replicas: 1
- Redis: ON (SPRING_CACHE_TYPE=redis)
- Kafka: ON
- Rate Limiting: ON
- Locust Workers: 5

### Результаты
| Метрика | Значение | vs Test A |
|---------|----------|-----------|
| Max Users до 5% ошибок | ~150-200 | -25% (rate limit) |
| Max RPS | ~16 | -16% |
| Final Error Rate | 21% | -64% (лучше) |
| Total Requests | 21,440 | -18% |
| Avg Latency | 8,026ms | -47% (лучше) |

### Улучшения от Redis
| Метрика | Test A | Test B | Улучшение |
|---------|--------|--------|-----------|
| GET ошибки | 40% | 16% | **2.5x лучше** |
| GET latency | 11-12 сек | 6-7 сек | **~2x быстрее** |

### Bottleneck
- **/api/auth/login: 86% ошибок** - BCrypt всё ещё CPU-bound
- Redis помог GET, но не LOGIN

---

## Test C: Scaling (WH-112)

**Дата:** 2025-11-30
**Конфигурация:**
- API Replicas: **2**
- Redis: ON
- Kafka: ON
- Rate Limiting: **OFF**
- API CPU Limit: **1000m** (было 500m)
- API Memory Limit: **1Gi** (было 512Mi)
- Redis maxclients: **10000**
- Locust Workers: **8**

### Результаты
| Метрика | Значение | vs Test A | vs Test B |
|---------|----------|-----------|-----------|
| Max Users до 5% ошибок | **500** | **+150%** | **+150%** |
| Max RPS | **55** | **+189%** | **+244%** |
| Final Error Rate | 5.25% | -91% | -75% |
| Total Requests | **84,874** | **+223%** | **+296%** |
| Avg Latency при 500u | 7,160ms | -53% | -11% |

### Прогресс по ступеням нагрузки

| Users | Test A | Test B | Test C | C vs A/B |
|-------|--------|--------|--------|----------|
| 10 | 5 RPS, 478ms | 5 RPS, 868ms | **7 RPS, 153ms** | 3-6x лучше |
| 25 | 8 RPS, ~600ms | 10 RPS, ~500ms | **14.5 RPS, 129ms** | 4-5x лучше |
| 50 | 12 RPS, ~1000ms | 15 RPS, ~800ms | **25.3 RPS, 127ms** | 6-8x лучше |
| 100 | 15 RPS, 1845ms, 1% err | 16 RPS, 1845ms, 1% err | **48.4 RPS, 232ms, 0%** | **8x лучше** |
| 150 | 18 RPS, 3000ms, 2% err | 15 RPS, 2500ms, 2% err | **42.8 RPS, 512ms, 0%** | 5-6x лучше |
| 200 | FAIL (6%+ err) | FAIL (6%+ err) | **39.2 RPS, ~1000ms, 0%** | Работает! |
| 300 | FAIL | FAIL | **~35 RPS, ~3000ms, 2%** | Работает! |
| 450 | FAIL | FAIL | **~10 RPS, ~5700ms, 3%** | Работает! |
| 500 | FAIL | FAIL | **~8 RPS, 7160ms, 5%** | Предел |

### Статистика по эндпоинтам (при 500 users)

| Endpoint | Requests | Failures | Fail% | Avg (ms) |
|----------|----------|----------|-------|----------|
| /api/auth/login | 548 | 35 | 6% | 20,745 |
| /api/auth/me | 8,935 | 458 | 5% | 7,290 |
| /api/products (GET) | 44,440 | 2,219 | 4% | 6,868 |
| /api/products (POST) | 11,606 | 666 | 5% | 7,499 |
| /api/products (PUT) | 1,046 | 45 | 4% | 7,457 |
| /api/products (DELETE) | 523 | 34 | 6% | 7,873 |
| /api/products?category | 17,720 | 999 | 5% | 7,165 |
| **TOTAL** | **84,874** | **4,456** | **5%** | **7,160** |

### Ключевое наблюдение
Ошибки распределены **равномерно** по всем эндпоинтам (4-6%), а не концентрируются на login.
Это означает, что 2 реплики успешно распределили BCrypt нагрузку!

---

## Test D: Extended Scaling (WH-113) - ЗАВЕРШЁН

**Дата:** 2025-11-30
**Статус:** Завершён, выявлен bottleneck PostgreSQL connections

### Конфигурация Test D
| Параметр | Test C | Test D | Изменение |
|----------|--------|--------|-----------|
| API Replicas | 2 | **4** | +100% |
| API CPU Limit | 1000m | 1000m | = |
| API Memory Limit | 1Gi | 1Gi | = |
| **HikariCP Pool** | 10 | **20** | +100% |
| HikariCP Min Idle | 10 | **5** | Оптимизация |
| Locust Workers | 8 | **12** | +50% |
| Rate Limiting | OFF | OFF | = |
| Redis maxclients | 10000 | 10000 | = |
| PostgreSQL max_connections | 100 | 100 | = |

**Total DB connections:** 4 pods × 20 = **80 max** (при PostgreSQL max=100 = **80% лимита**)

### Результаты Test D
| Метрика | Значение | vs Test C |
|---------|----------|-----------|
| Max Users до деградации | **~150-200** | **-60%** |
| Peak RPS | **71.7** (при 150u) | **+30%** |
| Total Requests | 89,722 | +6% |
| Final Error Rate | **0%** | Лучше |
| Avg Latency | 1,206ms | = |
| p95 Latency | 5,100ms | = |

### Прогресс по ступеням нагрузки
| Users | RPS | Errors | p95 (ms) | Состояние |
|-------|-----|--------|----------|-----------|
| 10 | 4.6 | 0% | ~400 | Стабильно |
| 25 | 11.9 | 0% | 400 | Стабильно |
| 50 | 25.2 | 0% | 160 | Стабильно |
| 100 | ~60 | 0% | ~800 | Стабильно |
| 150 | **71.7** | 0% | 1,000 | **Пик RPS** |
| 200 | ~65 | 0% | 2,000 | Деградация начинается |
| 300 | **50.9** | 0% | **6,100** | **Сильная деградация** |

### Статистика по эндпоинтам (Test D)
| Endpoint | Requests | Failures | Fail% | Avg (ms) | p95 (ms) |
|----------|----------|----------|-------|----------|----------|
| /api/auth/login | 300 | 0 | 0% | 6,968 | 15,000 |
| /api/auth/me | 9,000 | 0 | 0% | 555 | 2,600 |
| /api/products (GET) | 45,013 | 0 | 0% | 1,422 | 5,900 |
| /api/products (POST) | 12,522 | 0 | 0% | 1,276 | 4,900 |
| /api/products (PUT) | 1,133 | 0 | 0% | 1,356 | 5,100 |
| /api/products (DELETE) | 524 | 0 | 0% | 1,331 | 4,900 |
| /api/products?category | 18,201 | 0 | 0% | 975 | 4,200 |
| **TOTAL** | **89,722** | **0** | **0%** | **1,206** | **5,100** |

### Выявленный Bottleneck: PostgreSQL Connections

**Проблема:** При 300 users PostgreSQL достиг 81 соединений из 100 (81% лимита).

```
# Диагностика:
PostgreSQL max_connections: 100
Текущие соединения при 300u: 81
HikariCP: 4 pods × 20 = 80 max

# Эффект:
- HikariCP ждёт освобождения connections
- Latency растёт экспоненциально
- RPS падает с 71.7 до 50.9 (-29%)
```

### Сравнение Test C vs Test D
| Метрика | Test C (2 pods) | Test D (4 pods) | Вывод |
|---------|-----------------|-----------------|-------|
| Max Users | **500** | ~150-200 | 2 реплики лучше |
| Peak RPS | 55 | **71.7** | 4 реплики лучше на низкой нагрузке |
| DB Connections | 20 (20%) | 80 (80%) | Contention на БД |
| Bottleneck | CPU (BCrypt) | **DB Connections** | Смещение bottleneck |

---

## Выводы и рекомендации

### Что работает
1. **Горизонтальное масштабирование до 2-3 реплик** - главный фактор улучшения
2. **Redis кэширование** - улучшает GET операции на 2.5x
3. **Отключение rate limit** - убирает искусственные ограничения

### Выявленные Bottlenecks
1. **BCrypt (решено масштабированием)** - CPU-bound, распределяется по репликам
2. **PostgreSQL connection pool (Test D)** - при 4+ репликах DB connections становятся bottleneck
3. **Закон убывающей отдачи** - больше реплик ≠ лучше, если bottleneck смещается

### Оптимальная конфигурация (по результатам тестов)
| Параметр | Рекомендация | Обоснование |
|----------|--------------|-------------|
| API Replicas | **2-3** | Баланс CPU и DB connections |
| HikariCP Pool | **10-15** per pod | Суммарно 30-45 conn (30-45% от max) |
| PostgreSQL max_connections | 100-200 | Увеличить если нужно 4+ реплик |

### Варианты дальнейшей оптимизации
```
Вариант A: Уменьшить реплики до 2-3 (рекомендуется)
───────────────────────────────────────────────────
kubectl scale deployment/warehouse-api -n warehouse --replicas=2
# Ожидаемый результат: ~500 users, ~55 RPS

Вариант B: Увеличить PostgreSQL max_connections
───────────────────────────────────────────────
kubectl exec -n warehouse postgres-0 -- psql -U postgres \
  -c "ALTER SYSTEM SET max_connections = 200;"
# Позволит 4 репликам работать без contention

Вариант C: Добавить PgBouncer
─────────────────────────────
# Connection pooler мультиплексирует соединения
# Позволяет много реплик API с меньшим числом реальных соединений к БД

Вариант D: Уменьшить BCrypt cost factor
───────────────────────────────────────
# Изменение кода: cost 12 → 10
# Ускорит логин в ~4 раза, но снизит безопасность
```

### Рекомендации для Production
1. **2-3 реплики API** - оптимальный баланс для текущей конфигурации БД
2. **HPA (Horizontal Pod Autoscaler)** с maxReplicas=3 для автомасштабирования
3. **PgBouncer** если нужно больше 3 реплик API
4. **PostgreSQL read replica** для READ-heavy нагрузки
5. **Redis Cluster** для высокой доступности кэша

---

## Артефакты

| Файл | Описание |
|------|----------|
| `baseline_report.md` | Отчёт Test A |
| `baseline_stats.csv` | CSV данные Test A |
| `optimized_report.md` | Отчёт Test B |
| `optimized_stats.csv` | CSV данные Test B |
| `test_c_report.md` | Отчёт Test C |
| `test_c_stats.csv` | CSV данные Test C |
| `test_c_config.md` | Конфигурация Test C |
| `test_c_monitor.log` | Лог мониторинга Test C |
| `test_d_stats.csv` | CSV данные Test D |
| `locust_tool_report.md` | Анализ инструмента Locust |

---

*Последнее обновление: 2025-11-30 (добавлены результаты Test D)*
