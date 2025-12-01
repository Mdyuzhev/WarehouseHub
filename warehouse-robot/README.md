# Warehouse Robot

Симулятор складских операций для тестирования и демонстрации системы.

## Описание

Warehouse Robot эмулирует работу сотрудника склада, выполняя типичные операции:
- **Приёмка товара** — создание новых позиций на складе
- **Отгрузка** — уменьшение остатков по заказам
- **Инвентаризация** — корректировка и списание

## Архитектура

```
warehouse-robot/
├── api.py              # FastAPI приложение
├── robot.py            # CLI интерфейс
├── api_client.py       # HTTP клиент для Warehouse API
├── config.py           # Конфигурация (pydantic-settings)
├── scenarios/          # Сценарии работы
│   ├── base.py         # Базовый класс
│   ├── receiving.py    # Приёмка товара
│   ├── shipping.py     # Отгрузка
│   └── inventory.py    # Инвентаризация
├── Dockerfile
└── requirements.txt
```

## API Endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/` | Информация о сервисе |
| GET | `/health` | Health check |
| GET | `/status` | Текущий статус робота |
| GET | `/stats` | Статистика выполнения |
| GET | `/scenarios` | Список сценариев |
| POST | `/start` | Запуск сценария |
| POST | `/stop` | Остановка робота |

## Запуск сценария

```bash
# POST /start
curl -X POST http://localhost:8070/start \
  -H "Content-Type: application/json" \
  -d '{"scenario": "receiving", "speed": "fast"}'
```

Параметры:
- `scenario`: `receiving`, `shipping`, `inventory`
- `speed`: `slow`, `normal`, `fast`

## CLI

```bash
# Запуск сценария напрямую
python robot.py run receiving --speed fast

# Список сценариев
python robot.py list

# Проверка подключения к API
python robot.py status

# Запуск API сервера
python robot.py api --port 8070
```

## Конфигурация

Переменные окружения с префиксом `ROBOT_`:

| Переменная | Описание | Default |
|------------|----------|---------|
| `ROBOT_API_URL` | URL Warehouse API | `http://warehouse-api:8080` |
| `ROBOT_EMPLOYEE_USERNAME` | Логин сотрудника | `employee` |
| `ROBOT_EMPLOYEE_PASSWORD` | Пароль сотрудника | `password123` |
| `ROBOT_API_PORT` | Порт Robot API | `8070` |
| `ROBOT_TELEGRAM_BOT_URL` | URL Telegram бота | - |

## K8s Deployment

```bash
# Сборка образа
docker build -t warehouse-robot:latest .

# Импорт в k3s
docker save warehouse-robot:latest | sudo k3s ctr images import -

# Деплой
kubectl apply -k k8s/robot/
```

NodePort: `30070`

## Сценарии

### Приёмка (receiving)
- Создаёт 3-7 новых товаров
- Генерирует реалистичные названия (бренды, категории)
- Случайные количества и цены

### Отгрузка (shipping)
- Выбирает 2-5 товаров с количеством > 0
- Уменьшает остатки на 1-10 единиц
- Считает общую сумму отгрузки

### Инвентаризация (inventory)
- Корректирует количество (±5 единиц)
- 30% вероятность недостачи, 70% — излишки
- Списывает товары с нулевым остатком

## Telegram интеграция

Робот доступен через Telegram бота:
- Команда `/robot` или кнопка "🤖 Robot"
- Выбор сценария и скорости
- Просмотр статуса и статистики
- Защита паролем

## Мониторинг

```bash
# Логи
kubectl logs -n warehouse deployment/warehouse-robot -f

# Статус
curl http://localhost:30070/status

# Статистика
curl http://localhost:30070/stats
```
