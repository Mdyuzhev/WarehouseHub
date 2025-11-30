# WH-103: Baseline Load Test Report

**Дата:** 2025-11-30
**Режим:** BASELINE (без Redis/Kafka)
**Цель:** http://warehouse-api-service.warehouse.svc.cluster.local:8080

## Результаты

### Точка отказа
| Метрика | Значение |
|---------|----------|
| Max Users до отказа | ~200-300 |
| Users при критическом отказе | 400 |
| RPS при отказе | 19.1 |
| Error Rate | 59% |
| Avg Latency | 15,156 ms |

### Статистика по эндпоинтам

| Endpoint | Requests | Failures | Fail% | Avg (ms) |
|----------|----------|----------|-------|----------|
| /api/auth/login | 8,781 | 8,623 | **98%** | 22,386 |
| /api/auth/me | 1,856 | 724 | 39% | 12,866 |
| /api/products (GET) | 9,357 | 3,715 | 40% | 11,563 |
| /api/products (POST) | 2,337 | 856 | 37% | 10,777 |
| /api/products (PUT) | 182 | 61 | 34% | 7,765 |
| /api/products (DELETE) | 89 | 26 | 29% | 3,397 |
| /api/products?category | 3,695 | 1,485 | 40% | 11,637 |
| **TOTAL** | **26,297** | **15,490** | **59%** | **15,156** |

## Анализ

### Узкое место: /api/auth/login
- **98% ошибок** на логине
- Причина: BCrypt хэширование паролей - CPU-intensive операция
- При 400 users логин занимает **22 секунды** (таймаут)

### Рекомендации
1. **Redis кэширование сессий** - уменьшит нагрузку на /api/auth
2. **Увеличить bcrypt cost factor awareness** - оптимизировать для нагрузки
3. **Connection pooling** - для БД

## Вывод

**BASELINE максимум: ~200-300 concurrent users**

При превышении система деградирует из-за CPU-bound операций аутентификации.

---
*Следующий этап: Тест B - Optimized (с Redis/Kafka)*
