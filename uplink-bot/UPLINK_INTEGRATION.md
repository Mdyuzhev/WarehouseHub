# WarehouseHub Uplink Bot — архитектура и интеграция

Uplink-бот — SDK-бот для Uplink (Matrix-мессенджер). Подключается по WebSocket,
получает slash-команды из каналов, обрабатывает их локально на homelab и отправляет
ответы обратно через WS. Параллельно отправляет webhook-уведомления (CI, deploy, robot).

---

## Архитектура

```
WarehouseHub (homelab docker-compose)
  └── uplink-bot (Python/FastAPI + WebSocket client)
        │
        ├── WebSocket (outbound) ──► wss://uplink.wh-lab.ru/bot-ws/<token>
        │     ← получает /wh команды из каналов
        │     → отправляет ответы через WS action send_message
        │
        ├── bot/uplink.py (webhook) ──► https://uplink.wh-lab.ru/hooks/wh_ci
        │     → отправляет уведомления (deploy, robot, generic)
        │
        └── FastAPI :8001
              /health         — healthcheck
              /robot/notify   — уведомление от warehouse-robot
              /deploy/notify  — уведомление о деплое
              /send           — произвольное сообщение
```

**Ключевое решение:** бот подключается к Uplink по WebSocket (outbound).
NAT не мешает — соединение исходящее, как у Telegram long polling.

---

## Компоненты

### SDK Bot (WebSocket)

Модуль `bot/ws_bridge.py` — WebSocket-клиент с автореконнектом.

- Подключается к `wss://uplink.wh-lab.ru/bot-ws/<token>`
- Получает события: `{ type: "event", event: { type: "command", command: "/wh", args: [...] } }`
- Обрабатывает команды через `bot/commands.py:handle_command_text()`
- Отправляет ответ: `{ type: "action", action: "send_message", room_id, body }`

Протокол описан в `packages/bot-sdk/` репозитория Uplink.

### Webhook (уведомления)

Модуль `bot/uplink.py` — HTTP-клиент для отправки уведомлений.

- POST на `https://uplink.wh-lab.ru/hooks/wh_ci` с заголовком `X-Gitlab-Token`
- Форматы: `x-deploy-event: deploy`, `object_kind: notify`, `text/html`
- Бот `@bot_wh_ci:uplink.wh-lab.ru` пишет в комнату `WH_CI_NOTIFY_ROOM_ID`

### Команды `/wh`

| Команда       | Описание           |
|---------------|--------------------|
| `/wh status`  | Статус серверов     |
| `/wh pods`    | Docker-сервисы      |
| `/wh metrics` | CPU / RAM           |
| `/wh robot`   | Статус робота       |
| `/wh help`    | Список команд       |

Команды зарегистрированы у SDK custom bot в Uplink botservice.
В `registry.mjs` у `wh_ci` команды пустые — он только для webhook-уведомлений.

---

## Настройка

### Переменные окружения (uplink-bot)

| Переменная          | Описание                              | Пример                                              |
|---------------------|---------------------------------------|------------------------------------------------------|
| `UPLINK_WS_URL`     | WebSocket URL Uplink (без /bot-ws/)   | `wss://uplink.wh-lab.ru`                             |
| `UPLINK_BOT_TOKEN`  | Токен SDK-бота                        | `bot_9b9a057e...`                                    |
| `UPLINK_WEBHOOK_URL`| URL webhook для уведомлений           | `https://uplink.wh-lab.ru/hooks/wh_ci`               |
| `UPLINK_WEBHOOK_TOKEN`| Токен верификации webhook            | `warehouse-wh-ci-2026`                               |

### Переменные окружения (Uplink .env)

| Переменная             | Описание                              |
|------------------------|---------------------------------------|
| `WH_CI_NOTIFY_ROOM_ID`| Room ID комнаты для CI-уведомлений    |
| `WH_CI_WEBHOOK_TOKEN`  | Секрет для верификации webhook        |

### Создание SDK-бота в Uplink

SDK-бот создаётся через API:

```bash
curl -X POST https://uplink.wh-lab.ru/api/custom-bots \
  -H "Authorization: Bearer <matrix_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "WarehouseHub Bot",
    "mode": "sdk",
    "owner": "@admin:uplink.wh-lab.ru",
    "commands": [{"command": "/wh", "description": "Команды WarehouseHub"}]
  }'
```

Ответ содержит `token` — это `UPLINK_BOT_TOKEN`.

Добавить бота в комнату:

```bash
curl -X POST https://uplink.wh-lab.ru/api/custom-bots/<botId>/rooms \
  -H "Authorization: Bearer <matrix_token>" \
  -H "Content-Type: application/json" \
  -d '{"roomId": "!roomId:uplink.wh-lab.ru"}'
```

---

## Формат сообщений

Botservice рендерит HTML-разметку Matrix:

| Элемент      | HTML                              |
|--------------|-----------------------------------|
| Жирный       | `<b>текст</b>`                    |
| Курсив       | `<i>текст</i>`                    |
| Код          | `<code>значение</code>`           |
| Блок кода    | `<pre>код</pre>`                  |
| Ссылка       | `<a href="url">текст</a>`         |
| Перенос      | `<br/>`                           |

Для webhook-уведомлений используйте поля `text` (plaintext) и `html` (форматированный).
Для SDK-команд ответ — plaintext через `body` в `send_message` action.

---

## Тестирование

### Webhook

```bash
curl -X POST https://uplink.wh-lab.ru/hooks/wh_ci \
  -H "Content-Type: application/json" \
  -H "x-deploy-event: deploy" \
  -H "X-Gitlab-Token: warehouse-wh-ci-2026" \
  -d '{"status":"success","commit":{"message":"test","hash":"abc1234"},"elapsed":42}'
```

### SDK-команда

Напишите `/wh status` в канале Uplink, где подключён бот.
