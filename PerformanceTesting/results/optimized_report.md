# WH-110: Optimized Load Test Report

**Дата:** 2025-11-30
**Режим:** OPTIMIZED (Redis + Kafka)
**Цель:** http://warehouse-api-service.warehouse.svc.cluster.local:8080

## Результаты

### Точка отказа
| Метрика | Значение |
|---------|----------|
| Max Users до 3% ошибок | ~150-200 |
| Users при критическом отказе | 200+ |
| Error Rate (финал) | 20.8% |
| Avg Latency | 8,026 ms |
| p95 Latency | 37,000 ms |
| Total Requests | 21,440 |
| Total Failures | 4,465 |

### Статистика по эндпоинтам

| Endpoint | Requests | Failures | Fail% | Avg (ms) | p95 (ms) |
|----------|----------|----------|-------|----------|----------|
| /api/auth/login | 1,426 | 1,229 | **86%** | 23,683 | 133,000 |
| /api/auth/me | 2,150 | 335 | 16% | 7,413 | 40,000 |
| /api/products (GET) | 10,413 | 1,679 | 16% | 6,724 | 33,000 |
| /api/products (POST) | 2,906 | 486 | 17% | 7,159 | 33,000 |
| /api/products (PUT) | 256 | 47 | 18% | 6,516 | 35,000 |
| /api/products (DELETE) | 113 | 19 | 17% | 5,642 | 24,000 |
| /api/products?category | 4,172 | 666 | 16% | 7,007 | 34,000 |
| **TOTAL** | **21,440** | **4,465** | **21%** | **8,026** | **37,000** |

### Типы ошибок
| Тип | Количество |
|-----|------------|
| Connection Refused | ~2,600 |
| 429 Rate Limit | 322 |
| Connect Timeout | ~420 |
| Remote Disconnected | ~480 |
| 401 Unauthorized | 170 |
| 403 Forbidden | ~385 |
| 500 Server Error | ~75 |

## Потребление ресурсов Locust

| Pod | CPU | Memory |
|-----|-----|--------|
| locust-master | 10m | 38Mi |
| locust-worker-1 | 6m | 41Mi |
| locust-worker-2 | 11m | 43Mi |
| locust-worker-3 | 13m | 44Mi |
| locust-worker-4 | 10m | 42Mi |
| locust-worker-5 | 6m | 41Mi |
| **TOTAL** | **~60m (0.06 core)** | **~250Mi** |

## Анализ

### Улучшения по сравнению с Baseline
1. **GET операции**: ошибки 16% vs 40% в Baseline (**2.5x лучше**)
2. **Latency GET**: 6-7 сек vs 11-12 сек в Baseline (**~2x быстрее**)
3. **Деградация мягче**: 21% vs 59% общих ошибок

### Bottleneck: /api/auth/login
- **86% ошибок** на логине (BCrypt CPU-bound)
- Среднее время: 23 секунды
- Причины ошибок:
  - Connection Refused (608) - перегрузка
  - 429 Rate Limit (322) - защита от брутфорса
  - Connect Timeout (95) - таймауты

### Вывод
**OPTIMIZED максимум: ~150-200 concurrent users** (аналогично Baseline)

Redis кэширование улучшило:
- Latency GET операций (~2x)
- Стабильность под нагрузкой (16% vs 40% ошибок на GET)

НО bottleneck остаётся в аутентификации (BCrypt):
- CPU-bound операция не масштабируется Redis
- Требуется горизонтальное масштабирование API или оптимизация BCrypt cost

---
*Следующий этап: Сравнительный отчёт A/B тестирования*
