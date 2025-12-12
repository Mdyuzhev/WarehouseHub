# WH-105: Стратегия нагрузочного тестирования Warehouse API

## 1. Цели тестирования

### Основная цель
Определить максимальную пропускную способность Warehouse API и сравнить производительность в двух режимах:
- **Baseline**: без Redis кэширования и Kafka
- **Optimized**: с Redis кэширования и Kafka

### Метрики успеха
| Метрика | Порог | Критический |
|---------|-------|-------------|
| Error Rate | < 1% | > 3% = STOP |
| Response Time p95 | < 500ms | > 1500ms = STOP |
| Response Time p99 | < 1000ms | > 3000ms |

## 2. Тестовое окружение

### Инфраструктура
- **Кластер**: K3s на 192.168.1.74
- **Namespace**: warehouse (API), loadtest (Locust)
- **API Endpoint**: http://warehouse-api-service.warehouse.svc.cluster.local:8080

### Компоненты
| Компонент | Baseline | Optimized |
|-----------|----------|-----------|
| PostgreSQL | ✓ | ✓ |
| Redis | ✗ | ✓ |
| Kafka | ✗ | ✓ |

## 3. Профиль нагрузки

### StepLoadShape
```
Фаза 1 (0-60 мин): Постепенный рост
├── 0-5 мин:   10 users  (spawn_rate=5)
├── 5-10 мин:  25 users  (spawn_rate=5)
├── 10-15 мин: 50 users  (spawn_rate=10)
├── 15-20 мин: 100 users (spawn_rate=15)
├── 20-25 мин: 150 users (spawn_rate=20)
├── 25-30 мин: 200 users (spawn_rate=20)
├── 30-35 мин: 250 users (spawn_rate=20)
├── 35-40 мин: 300 users (spawn_rate=25)
├── 40-45 мин: 350 users (spawn_rate=25)
├── 45-50 мин: 400 users (spawn_rate=25)
├── 50-55 мин: 450 users (spawn_rate=25)
└── 55-60 мин: 500 users (spawn_rate=30)

Фаза 2 (60+ мин): Агрессивный рост (+150 users каждые 2 мин)
├── 60-62 мин: 650 users
├── 62-64 мин: 800 users
├── ...
└── 78-80 мин: 2000 users (максимум)
```

### Распределение ролей (weights)
| Роль | Weight | Описание |
|------|--------|----------|
| SuperUser | 1 | CRUD все операции |
| Admin | 2 | Только чтение |
| Manager | 3 | Только чтение |
| Employee | 5 | Создание товаров |

### Сценарии (tasks)
| Endpoint | Weight | Описание |
|----------|--------|----------|
| GET /api/products | 5 | Список товаров |
| GET /api/products?category | 2 | Фильтр по категории |
| POST /api/products | 3 | Создание товара |
| PUT /api/products/{id} | 2 | Обновление товара |
| DELETE /api/products/{id} | 1 | Удаление товара |
| GET /api/auth/me | 1 | Текущий пользователь |

## 4. Критерии остановки

### Автоматические (мониторинг)
- Error Rate > 3% в течение 2+ минут
- p95 Response Time > 1500ms в течение 2+ минут
- Система не отвечает (connection refused)

### Ручные
- Достигнут максимум профиля (2000 users)
- Время теста > 80 минут

## 5. План тестирования

### Тест A: Baseline
1. Убедиться что Redis/Kafka отключены
2. Сбросить статистику Locust
3. Запустить StepLoadShape
4. Мониторить каждые 10 минут
5. Остановить при достижении критериев
6. Сохранить результаты

### Тест B: Optimized
1. Включить Redis кэширование
2. Включить Kafka
3. Перезапустить API
4. Повторить шаги 2-6 из Теста A

### Сравнительный анализ
- Сравнить max users до 3% ошибок
- Сравнить RPS при одинаковой нагрузке
- Сравнить latency (p50, p95, p99)
- Определить улучшение в %

## 6. Артефакты

### Входные
- `configs/locustfile.py` - сценарии
- `configs/api-baseline.yaml` - ConfigMap baseline
- `configs/api-optimized.yaml` - ConfigMap optimized
- `scripts/switch-mode.sh` - переключение режимов

### Выходные
- `results/baseline_report.md` - отчёт Baseline
- `results/baseline_stats.csv` - сырые данные
- `results/optimized_report.md` - отчёт Optimized
- `results/optimized_stats.csv` - сырые данные
- `results/comparison_report.md` - сравнительный анализ

## 7. Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| Тест на проде | Высокая | Проверять host перед запуском |
| Переполнение БД | Средняя | Cleanup в on_stop() |
| Таймауты bcrypt | Высокая | Известное ограничение, фиксируем |
| K8s OOM | Средняя | Мониторинг ресурсов |

## 8. Ответственные

- **Исполнитель**: QA Team
- **Инфраструктура**: DevOps
- **Анализ результатов**: QA + Dev

---
*Документ создан: 2025-11-30*
*Задача: WH-105*
