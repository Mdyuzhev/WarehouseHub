# Подключение к Uplink — руководство для разработчика бота

Этот документ описывает, как адаптировать существующий Python-бот для параллельной
отправки уведомлений в Uplink. Рассматривается на примере WarehouseHub telegram-bot,
но подход универсален для любого Python-сервиса с HTTP-клиентом.

---

## Как это работает

В Uplink развёрнут `uplink-botservice` — Node.js Application Service для Matrix Synapse.
Он регистрирует виртуальных бот-пользователей (`@bot_ci:uplink.wh-lab.ru` и др.)
и принимает webhook-запросы от внешних систем по адресу:

```
POST https://uplink.wh-lab.ru/hooks/<integration_id>
```

Маршрут `/hooks/ci` уже реализован — `handlers/ci.mjs` умеет принимать события
от GitLab CI, GitHub Actions и деплой-скриптов, форматировать их и отправлять
сообщения от `@bot_ci` в нужные комнаты.

Для подключения Python-бота нужно три шага:

1. Получить `Room ID` целевой комнаты (например, `#CI` в пространстве WAREHOUSE).
2. Прописать `CI_NOTIFY_ROOM_ID` и `GITLAB_WEBHOOK_TOKEN` в `.env` Uplink.
3. Добавить в Python-бот класс `UplinkNotifier` и вызывать его там, где сейчас пишется в Telegram.

Бот **не** обращается напрямую к Matrix API — только к HTTP-эндпоинту botservice,
который уже знает как отправить сообщение от имени нужного бота в нужную комнату.

---

## Шаг 1. Получить Room ID

Откройте настройки нужной комнаты в Uplink — нажмите значок шестерёнки рядом
с названием канала или комнаты в сайдбаре. Во вкладке **Информация** скопируйте
поле **Internal Room ID**. Оно выглядит так:

```
!lcvmJcVFFAPWaFHXfh:uplink.wh-lab.ru
```

Именно это значение нужно передать в переменную `CI_NOTIFY_ROOM_ID`.

---

## Шаг 2. Настроить .env Uplink

Откройте файл `E:\Uplink\docker\.env` и добавьте две строки:

```dotenv
# Room ID комнаты #CI в пространстве WAREHOUSE
CI_NOTIFY_ROOM_ID=!lcvmJcVFFAPWaFHXfh:uplink.wh-lab.ru

# Секрет для верификации webhook-запросов от GitLab
GITLAB_WEBHOOK_TOKEN=warehouse-ci-uplink-2026
```

После этого передеплойте botservice:

```bash
# На сервере
cd ~/projects/uplink
docker compose -f docker-compose.production.yml up -d --no-deps uplink-botservice
```

Botservice при старте автоматически войдёт в указанную комнату от имени `@bot_ci`
и будет готов принимать уведомления.

---

## Шаг 3. Добавить UplinkNotifier в Python-бот

### 3.1. Создать модуль `bot/uplink.py`

Создайте файл рядом с `bot/telegram.py`. Архитектура намеренно повторяет telegram.py —
те же async-функции, тот же httpx, чтобы в коде бота замена выглядела симметрично.

```python
"""
Клиент для отправки уведомлений в Uplink через botservice webhook API.
Архитектурно аналогичен bot/telegram.py — заменяет Telegram как канал доставки.
"""

import logging
import httpx
from config import UPLINK_WEBHOOK_URL, UPLINK_WEBHOOK_TOKEN

logger = logging.getLogger(__name__)


async def send_message(text: str, html: str = None) -> bool:
    """
    Отправляет уведомление в Uplink.

    text  — plaintext-версия (обязательна, используется как fallback).
    html  — HTML-версия для красивого отображения в Matrix-клиентах (опциональна).

    Формат payload совпадает с тем, что botservice ожидает от деплой-скриптов.
    """
    if not UPLINK_WEBHOOK_URL:
        logger.warning("UPLINK_WEBHOOK_URL не задан, уведомление пропущено")
        return False

    payload = {
        "object_kind": "notify",           # произвольное поле — ci.mjs не смотрит на него
        "text": text,
        "html": html or text,
    }

    headers = {}
    if UPLINK_WEBHOOK_TOKEN:
        # botservice проверяет X-Gitlab-Token для /hooks/ci
        headers["X-Gitlab-Token"] = UPLINK_WEBHOOK_TOKEN

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                UPLINK_WEBHOOK_URL,
                json=payload,
                headers=headers,
            )
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Uplink webhook вернул {response.status_code}: {response.text}")
                return False
    except httpx.TimeoutException:
        logger.warning("Timeout при отправке уведомления в Uplink")
        return False
    except Exception as e:
        logger.error(f"Ошибка отправки в Uplink: {e}")
        return False


async def send_deploy_event(
    status: str,           # "success" или "failure"
    commit_message: str = "",
    commit_hash: str = "",
    commit_author: str = "",
    elapsed: float = None,
    error: str = None,
) -> bool:
    """
    Отправляет событие деплоя в формате, который ci.mjs обрабатывает нативно.
    Это тот же формат, который использует deploy-prod.sh через заголовок x-deploy-event.
    """
    if not UPLINK_WEBHOOK_URL:
        return False

    payload = {
        "status": status,
        "commit": {
            "message": commit_message,
            "hash": commit_hash,
            "author": commit_author,
        },
    }
    if elapsed is not None:
        payload["elapsed"] = elapsed
    if error:
        payload["error"] = error

    headers = {"x-deploy-event": "deploy"}
    if UPLINK_WEBHOOK_TOKEN:
        headers["X-Gitlab-Token"] = UPLINK_WEBHOOK_TOKEN

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                UPLINK_WEBHOOK_URL,
                json=payload,
                headers=headers,
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Ошибка отправки deploy event в Uplink: {e}")
        return False
```

### 3.2. Добавить переменные в `config.py`

Добавьте в конец файла новую секцию:

```python
# =============================================================================
# Uplink (Matrix messenger)
# =============================================================================
# URL вида: https://uplink.wh-lab.ru/hooks/ci
UPLINK_WEBHOOK_URL = os.getenv("UPLINK_WEBHOOK_URL", "")
# Должен совпадать с GITLAB_WEBHOOK_TOKEN в .env Uplink
UPLINK_WEBHOOK_TOKEN = os.getenv("UPLINK_WEBHOOK_TOKEN", "")
```

### 3.3. Обновить `.env.example`

Добавьте в `.env.example` документацию новых переменных:

```dotenv
# =============================================================================
# Uplink (Matrix messenger) — параллельные уведомления
# =============================================================================
# URL webhook-эндпоинта botservice: https://uplink.wh-lab.ru/hooks/ci
UPLINK_WEBHOOK_URL=https://uplink.wh-lab.ru/hooks/ci
# Секрет должен совпадать с GITLAB_WEBHOOK_TOKEN в docker/.env Uplink
UPLINK_WEBHOOK_TOKEN=warehouse-ci-uplink-2026
```

---

## Шаг 4. Интегрировать в app.py

Uplink работает параллельно с Telegram — не вместо него. Используйте `asyncio.gather`
чтобы оба уведомления отправлялись одновременно без взаимной блокировки.

```python
# В начале app.py добавить импорт
from bot import uplink

# Пример: модифицировать robot_notify endpoint
@app.post("/robot/notify")
async def robot_notify(notification: RobotNotification):
    try:
        logger.info(f"Received robot notification: scenario={notification.scenario}")
        message = format_robot_notification(notification.scenario, notification.result)

        # Отправляем параллельно в Telegram и Uplink
        await asyncio.gather(
            send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown"),
            uplink.send_message(text=message),          # plaintext fallback
            return_exceptions=True,                      # один канал не блокирует другой
        )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Robot notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

`return_exceptions=True` критически важен: если Uplink недоступен, бот не упадёт
и Telegram-уведомление всё равно дойдёт.

---

## Шаг 5. Запустить рядом с Telegram-ботом

Дополнительных контейнеров не нужно — `UplinkNotifier` работает внутри существующего
процесса telegram-bot. Достаточно добавить переменные в `docker-compose.yml`
WarehouseHub-проекта.

Найдите сервис `telegram-bot` в вашем `docker-compose.yml` и добавьте переменные:

```yaml
services:
  telegram-bot:
    build: ./telegram-bot
    environment:
      # ... существующие переменные ...
      UPLINK_WEBHOOK_URL: ${UPLINK_WEBHOOK_URL:-}
      UPLINK_WEBHOOK_TOKEN: ${UPLINK_WEBHOOK_TOKEN:-}
```

Добавьте значения в `.env` WarehouseHub-проекта:

```dotenv
UPLINK_WEBHOOK_URL=https://uplink.wh-lab.ru/hooks/ci
UPLINK_WEBHOOK_TOKEN=warehouse-ci-uplink-2026
```

---

## Тестирование

### Проверить что botservice принимает запросы

```bash
# Тест — отправить событие успешного деплоя вручную
curl -X POST https://uplink.wh-lab.ru/hooks/ci \
  -H "Content-Type: application/json" \
  -H "x-deploy-event: deploy" \
  -H "X-Gitlab-Token: warehouse-ci-uplink-2026" \
  -d '{
    "status": "success",
    "commit": {
      "message": "Тест уведомления из WarehouseHub",
      "hash": "abc1234",
      "author": "developer"
    },
    "elapsed": 42
  }'
```

Ожидаемый ответ: `{"ok": true}` или `{"status": "ok"}`.
В комнате `#CI` появится сообщение от `@bot_ci`.

### Проверить из Python

```python
import asyncio
from bot.uplink import send_deploy_event

asyncio.run(send_deploy_event(
    status="success",
    commit_message="Тест из Python",
    commit_hash="abc1234",
    elapsed=15.3,
))
```

---

## Формат сообщений в Uplink

Botservice рендерит сообщения как HTML-разметку Matrix. Для красивого отображения
используйте HTML-теги в поле `html`:

| Элемент      | HTML                              | Результат                  |
|--------------|-----------------------------------|----------------------------|
| Жирный текст | `<b>текст</b>`                    | **текст**                  |
| Курсив       | `<i>текст</i>`                    | *текст*                    |
| Код          | `<code>значение</code>`           | `значение`                 |
| Блок кода    | `<pre>многострочный\nкод</pre>`   | блок с моноширинным шрифтом |
| Ссылка       | `<a href="url">текст</a>`         | кликабельная ссылка         |
| Перенос      | `<br/>`                           | новая строка               |

Пример форматированного уведомления:

```python
html = (
    "<b>✅ Деплой WarehouseHub успешен</b><br/>"
    "📦 <code>abc1234</code> Fix: исправлен Robot API timeout <i>(developer)</i><br/>"
    "⏱️ 42 секунды"
)
await uplink.send_message(text="✅ Деплой успешен — abc1234", html=html)
```

---

## Архитектура итогового решения

```
WarehouseHub (docker-compose)
  └── telegram-bot (Python/FastAPI)
        ├── bot/telegram.py  →  api.telegram.org  →  Telegram-чат
        └── bot/uplink.py    →  uplink.wh-lab.ru/hooks/ci
                                      │
                                      ▼
                            uplink-botservice (Node.js)
                                      │
                                      ▼ Matrix event
                            Synapse (@bot_ci:uplink.wh-lab.ru)
                                      │
                                      ▼
                            Комната #CI в пространстве WAREHOUSE
```

Оба канала работают независимо. Если один недоступен — другой продолжает работу.
