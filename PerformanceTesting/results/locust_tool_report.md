# Отчёт по инструменту нагрузочного тестирования: Locust

**Дата:** 2025-11-30
**Версия:** Locust в K8s (распределённый режим)
**Задача:** WH-103 A/B тестирование

## 1. Конфигурация Locust

### Архитектура развёртывания
```
┌─────────────────────────────────────────────────────────┐
│                    K8s Namespace: loadtest              │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐                                    │
│  │  locust-master  │ ← Координатор, Web UI              │
│  │   (1 replica)   │   NodePort: 30089                  │
│  └────────┬────────┘                                    │
│           │                                             │
│  ┌────────┴────────┐                                    │
│  │  locust-workers │ ← Генерация нагрузки               │
│  │   (5 replicas)  │   ~40 users на worker              │
│  └─────────────────┘                                    │
│                                                         │
│  ┌─────────────────┐                                    │
│  │ locust-exporter │ ← Prometheus метрики               │
│  │   (1 replica)   │                                    │
│  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
```

### Компоненты
| Компонент | Replicas | Назначение |
|-----------|----------|------------|
| locust-master | 1 | Координация, Web UI, агрегация статистики |
| locust-worker | 5 | Генерация HTTP-запросов |
| locust-exporter | 1 | Экспорт метрик в Prometheus |

## 2. Потребление ресурсов

### При пиковой нагрузке (~200 concurrent users)

| Pod | CPU | Memory | CPU% от ноды |
|-----|-----|--------|--------------|
| locust-master | 10m | 38Mi | 0.08% |
| locust-worker-1 | 6m | 41Mi | 0.05% |
| locust-worker-2 | 11m | 43Mi | 0.09% |
| locust-worker-3 | 13m | 44Mi | 0.1% |
| locust-worker-4 | 10m | 42Mi | 0.08% |
| locust-worker-5 | 6m | 41Mi | 0.05% |
| locust-exporter | 4m | 13Mi | 0.03% |
| **TOTAL** | **~60m** | **~262Mi** | **~0.5%** |

### Сравнение с тестируемой системой

| Компонент | CPU | Memory |
|-----------|-----|--------|
| **Locust (весь кластер)** | **60m** | **262Mi** |
| warehouse-api | 497m | 495Mi |
| postgres | 31m | 51Mi |
| redis | 23m | 11Mi |
| kafka | 11m | 562Mi |

**Вывод:** Locust потребляет **~10%** ресурсов от тестируемой системы. Это приемлемо для нагрузочного тестирования.

## 3. Характеристики генерации нагрузки

### Распределение нагрузки по workers

```
Worker 1: ~40 virtual users (SuperUser, Admin, Manager, Employee)
Worker 2: ~40 virtual users
Worker 3: ~40 virtual users
Worker 4: ~40 virtual users
Worker 5: ~40 virtual users
─────────────────────────────
TOTAL:    ~200 virtual users
```

### Профиль нагрузки (StepLoadShape)

| Фаза | Время | Users | Spawn Rate |
|------|-------|-------|------------|
| Warmup | 0-5 мин | 10 | 5/сек |
| Ramp-up | 5-30 мин | 25→200 | 5-20/сек |
| Stress | 30-60 мин | 200→500 | 20-30/сек |
| Spike | 60+ мин | 500→2000 | 50/сек |

### Сценарии (task weights)

| Task | Weight | Описание |
|------|--------|----------|
| GET /api/products | 5 | Список товаров |
| POST /api/products | 3 | Создание товара |
| GET /api/products?category | 2 | Фильтрация |
| PUT /api/products/{id} | 2 | Обновление |
| DELETE /api/products/{id} | 1 | Удаление |
| GET /api/auth/me | 1 | Текущий пользователь |

## 4. Ограничения Locust

### Выявленные в ходе тестирования

| Ограничение | Описание | Влияние |
|-------------|----------|---------|
| Python GIL | Однопоточность на worker | Требует больше workers для высокой нагрузки |
| HTTP-only | Только HTTP/HTTPS протокол | Нет WebSocket, gRPC без плагинов |
| Greenlet overhead | Cooperative multitasking | При долгих запросах (BCrypt) greenlets блокируются |
| Memory per user | ~2-5KB на virtual user | При 10k+ users требуется много RAM |

### Максимальная производительность (наблюдаемая)

| Метрика | Значение | Условия |
|---------|----------|---------|
| Max RPS | ~15-20 | При 100-150 users, 0% errors |
| Max concurrent users | ~200 | До критических ошибок |
| Sustained RPS | ~5-10 | При стабильной работе |

## 5. Сравнение с альтернативами

| Инструмент | Язык | RPS на 1 core | Протоколы | Сценарии |
|------------|------|---------------|-----------|----------|
| **Locust** | Python | ~1-2k | HTTP | Python код |
| wrk | C | ~50-100k | HTTP | Lua скрипты |
| k6 | Go | ~5-10k | HTTP, WS, gRPC | JavaScript |
| Gatling | Scala | ~5-10k | HTTP, WS | Scala DSL |
| vegeta | Go | ~10-20k | HTTP | CLI/JSON |
| JMeter | Java | ~1-2k | HTTP, JDBC, etc | XML/GUI |

### Когда использовать Locust

✅ **Подходит для:**
- Функциональное нагрузочное тестирование
- Сложные пользовательские сценарии
- Интеграция с Python-экосистемой
- Распределённое тестирование
- Быстрое прототипирование

❌ **Не подходит для:**
- Benchmark чистой производительности сервера
- Тестирование на уровне соединений (C10K)
- Низкоуровневое профилирование latency
- Высоконагруженные синтетические тесты

## 6. Рекомендации

### Для данного проекта

1. **Locust достаточен** для A/B тестирования Redis/Kafka
2. **Для точных бенчмарков** рекомендуется:
   - `wrk` - для измерения max RPS на эндпоинт
   - `k6` - для сложных сценариев с высокой нагрузкой
   - `vegeta` - для стресс-тестирования

### Оптимизация Locust

```yaml
# Увеличить workers для большей нагрузки
kubectl scale deployment/locust-worker -n loadtest --replicas=10

# Увеличить ресурсы workers
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

## 7. Артефакты

| Файл | Описание |
|------|----------|
| `configs/locustfile.py` | Сценарии тестирования |
| `results/baseline_stats.csv` | Данные Baseline теста |
| `results/optimized_stats.csv` | Данные Optimized теста |
| `results/baseline_report.md` | Отчёт Baseline |
| `results/optimized_report.md` | Отчёт Optimized |

---
*Документ создан: 2025-11-30*
*Задача: WH-103*
