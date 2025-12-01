# Release Notes: WH-120, WH-121 & WH-122

**Дата релиза:** 2025-12-01
**Версия:** 1.5.0
**Задачи YouTrack:** WH-120, WH-121, WH-122 (bug fix)

---

## Обзор

Этот релиз добавляет две крупные функциональности:
1. **Warehouse Robot** — симулятор складских операций с интеграцией в Telegram
2. **Analytics Service** — real-time аналитика событий через Kafka

---

## WH-120: Warehouse Robot + Telegram интеграция

### Новые компоненты

#### Warehouse Robot Service (порт 30070)
- **Описание:** FastAPI-сервис симулятора складских операций
- **Расположение:** `/warehouse-robot/`
- **Docker образ:** `warehouse-robot:latest`
- **K8s namespace:** `warehouse`

#### API Endpoints
| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/` | GET | Информация о сервисе |
| `/health` | GET | Health check |
| `/start` | POST | Запуск сценария |
| `/stop` | POST | Остановка робота |
| `/status` | GET | Текущий статус |
| `/stats` | GET | Статистика выполнения |
| `/scenarios` | GET | Список сценариев |

#### Доступные сценарии
1. **receiving** — Приёмка товара (создание новых позиций)
2. **shipping** — Отгрузка (уменьшение остатков)
3. **inventory** — Инвентаризация (корректировка и списание)

#### Скорости выполнения
- `slow` — 3-5 секунд между действиями
- `normal` — 1-3 секунды между действиями
- `fast` — 0.3-1 секунда между действиями

### Telegram Bot интеграция

#### Новые команды
- `/robot` — Меню управления роботом
- Inline-кнопки для запуска/остановки сценариев
- Выбор скорости выполнения
- Просмотр статуса и статистики

#### Уведомления
После завершения каждого сценария робот отправляет уведомление в Telegram с результатами:
- Количество созданных/изменённых товаров
- Общее количество единиц
- Сумма операции

#### Endpoint для уведомлений
```
POST /robot/notify
```
Используется роботом для отправки результатов в чат.

### Файлы

```
warehouse-robot/
├── api.py              # FastAPI приложение
├── api_client.py       # Клиент Warehouse API
├── config.py           # Конфигурация
├── robot.py            # Главный модуль
├── Dockerfile          # Docker сборка
├── requirements.txt    # Зависимости
└── scenarios/
    ├── __init__.py     # Реестр сценариев
    ├── base.py         # Базовый класс
    ├── receiving.py    # Приёмка
    ├── shipping.py     # Отгрузка
    └── inventory.py    # Инвентаризация

k8s/robot/
├── kustomization.yaml  # Kustomize конфигурация
├── robot-deployment.yaml
├── robot-service.yaml
└── robot-secrets.yaml

telegram-bot/bot/handlers/
├── robot.py            # Обработчики команд робота
└── (изменения в __init__.py, app.py)

telegram-bot/services/
└── robot.py            # HTTP клиент для Robot API
```

---

## WH-121: Real-time Kafka Analytics Dashboard

### Новые компоненты

#### Analytics Service (порт 30091)
- **Описание:** FastAPI + WebSocket сервис аналитики
- **Расположение:** `/analytics-service/`
- **Docker образ:** `analytics-service:latest`
- **K8s namespace:** `warehouse`
- **Зависимости:** Kafka, Redis

#### API Endpoints
| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/health` | GET | Health check |
| `/api/stats` | GET | Агрегированная статистика |
| `/api/events` | GET | Последние события |
| `/api/hourly` | GET | Почасовая статистика |
| `/api/daily` | GET | Дневная статистика |
| `/api/categories` | GET | Статистика по категориям |
| `/ws` | WebSocket | Real-time обновления |

#### Kafka Topics
- `warehouse.audit` — События аудита (CRUD операции)
- `warehouse.notifications` — Уведомления о низких остатках

### Backend изменения (Java)

#### Новая роль ANALYST
Добавлена роль `ANALYST` в систему ролей:
- Файл: `User.java` (enum Role)
- Файл: `SecurityConfig.java` (настройка доступа)

#### Права доступа к /analytics
- SUPER_USER ✅
- ADMIN ✅
- MANAGER ✅
- ANALYST ✅

### Frontend изменения (Vue.js)

#### Новая страница /analytics
- **Расположение:** `/frontend/src/views/AnalyticsView.vue`
- **Роут:** `/analytics` (требует авторизации)

#### Компоненты дашборда
1. **Stats Cards** — Карточки с метриками
   - Total Events
   - Audit Events
   - Notifications
   - Stock Alerts

2. **Live Feed** — Лента событий в реальном времени
   - Анимация новых событий
   - Цветовая индикация по типу

3. **Audit Operations Chart** — Bar chart операций аудита
   - Create, Update, Delete, Login, Logout

4. **Time Charts** — Графики по времени
   - Почасовая статистика
   - Дневная статистика

5. **Categories Chart** — Статистика по категориям товаров

#### WebSocket
- Автоматическое подключение при загрузке страницы
- Автоматический реконнект при потере соединения
- Индикатор статуса подключения

### Файлы

```
analytics-service/
├── main.py             # FastAPI + WebSocket + Kafka consumer
├── config.py           # Конфигурация
├── Dockerfile
└── requirements.txt

k8s/analytics/
├── kustomization.yaml
├── analytics-deployment.yaml
└── analytics-service.yaml

frontend/src/
├── views/AnalyticsView.vue   # Страница аналитики
├── router/index.js           # Роут /analytics
└── components/analytics/     # Компоненты (если есть)
```

---

## WH-122: Bug fix — Расписание и наименования товаров

### Добавлен запуск по расписанию

#### Новые API Endpoints
| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/schedule` | POST | Запланировать сценарий на время |
| `/scheduled` | GET | Список запланированных задач |
| `/scheduled/{task_id}` | DELETE | Отменить задачу |

#### Формат запроса `/schedule`
```json
{
  "scenario": "receiving",
  "scheduled_time": "14:30",  // или "2025-12-01T14:30:00"
  "speed": "normal"
}
```

#### Telegram Bot интеграция
- Новая кнопка "⏰ Запланировать" в меню робота
- Выбор времени: +5/15/30 мин, +1/2/6 часов
- Ручной ввод времени (HH:MM)
- Просмотр и отмена запланированных задач

### Наименования товаров в уведомлениях

Уведомления теперь содержат список товаров:
```
📦 *Приёмка завершена*

Создано товаров: 4
Всего единиц: 133
На сумму: 1 066 692,58 ₽

*Товары:*
  • Ножницы офисные (36 шт)
  • Джинсы белый (19 шт)
  • Кроссовки Huawei (65 шт)
  • Тетрадь 96 листов (13 шт)
```

---

## Исправления во время релиза

### Проблема: Robot Service недоступен снаружи кластера

**Симптом:** `curl http://192.168.1.74:30070/health` возвращает пустой ответ

**Причина:** Рассогласование меток между Pod и Service selector.
- Service был применён через Kustomize с `commonLabels` (добавляет `app.kubernetes.io/*`)
- Deployment был применён напрямую без Kustomize

**Решение:** Переприменить все ресурсы через Kustomize:
```bash
kubectl delete deployment warehouse-robot -n warehouse
kubectl delete svc warehouse-robot-service -n warehouse
kubectl apply -k k8s/robot/
```

**Файл:** `k8s/robot/kustomization.yaml` — содержит `commonLabels`, которые добавляются и в selector сервиса.

---

## Конфигурация

### Переменные окружения Robot

| Переменная | Значение | Описание |
|------------|----------|----------|
| `ROBOT_API_URL` | `http://warehouse-api-service:8080` | URL Warehouse API |
| `ROBOT_EMPLOYEE_USERNAME` | (secret) | Логин сотрудника |
| `ROBOT_EMPLOYEE_PASSWORD` | (secret) | Пароль сотрудника |
| `ROBOT_TELEGRAM_BOT_URL` | `http://gitlab-telegram-bot:8000` | URL Telegram Bot |
| `ROBOT_SPEED_*` | различные | Задержки для скоростей |

### Переменные окружения Analytics

| Переменная | Значение | Описание |
|------------|----------|----------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka брокер |
| `REDIS_HOST` | `redis` | Redis хост |
| `REDIS_PORT` | `6379` | Redis порт |

---

## Проверка работоспособности

### Robot
```bash
# Health check
curl http://192.168.1.74:30070/health

# Запуск сценария
curl -X POST http://192.168.1.74:30070/start \
  -H "Content-Type: application/json" \
  -d '{"scenario":"receiving","speed":"fast"}'

# Статус
curl http://192.168.1.74:30070/status

# Статистика
curl http://192.168.1.74:30070/stats
```

### Analytics
```bash
# Health check
curl http://192.168.1.74:30091/health

# Статистика
curl http://192.168.1.74:30091/api/stats

# События
curl http://192.168.1.74:30091/api/events
```

### Telegram Bot
```
/robot — открыть меню робота
```

### Frontend
```
http://192.168.1.74:30081/analytics — страница аналитики
```

---

## Доступы

| Сервис | URL | Порт |
|--------|-----|------|
| Warehouse API | http://192.168.1.74:30080 | 30080 |
| Warehouse Frontend | http://192.168.1.74:30081 | 30081 |
| Warehouse Robot | http://192.168.1.74:30070 | 30070 |
| Analytics Service | http://192.168.1.74:30091 | 30091 |
| Telegram Bot | http://192.168.1.74:30088 | 30088 |

---

## Известные особенности

1. **Kustomize commonLabels** — При использовании `commonLabels` в kustomization.yaml метки добавляются и в селекторы сервисов. Все ресурсы должны применяться через `kubectl apply -k`, а не напрямую.

2. **Robot пароль** — Для запуска сценариев через Telegram требуется пароль (настраивается в `ROBOT_PASSWORD`).

3. **WebSocket реконнект** — Analytics dashboard автоматически переподключается к WebSocket при потере соединения.

---

## Авторы

- Разработка: Claude Code + flomaster
- Дата: 2025-12-01
