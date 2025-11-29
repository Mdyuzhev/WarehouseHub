# Test Payloads для GitLab Webhook

Это тестовые payload'ы для проверки webhook без реального GitLab.

## Файлы

- `pipeline_success.json` - успешный pipeline
- `pipeline_failed.json` - упавший pipeline
- `job_success.json` - успешная job
- `job_failed.json` - упавшая job (бот попытается получить лог)

## Использование

### Вариант 1: Скрипт (рекомендуется)

```bash
cd /home/flomaster/warehouse-master/telegram-bot
./test_webhook.sh
```

Выбери нужный тест из меню.

### Вариант 2: Ручной curl

```bash
# Pipeline Success
curl -X POST http://localhost:8000/webhook/gitlab \
  -H "Content-Type: application/json" \
  -d @test_payloads/pipeline_success.json

# Pipeline Failed
curl -X POST http://localhost:8000/webhook/gitlab \
  -H "Content-Type: application/json" \
  -d @test_payloads/pipeline_failed.json

# Job Success
curl -X POST http://localhost:8000/webhook/gitlab \
  -H "Content-Type: application/json" \
  -d @test_payloads/job_success.json

# Job Failed (с попыткой получить лог)
curl -X POST http://localhost:8000/webhook/gitlab \
  -H "Content-Type: application/json" \
  -d @test_payloads/job_failed.json
```

### Вариант 3: Из K8s

Если бот работает в кластере:

```bash
kubectl run -it --rm webhook-test --image=curlimages/curl --restart=Never -- \
  curl -X POST \
  http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab \
  -H "Content-Type: application/json" \
  -d @/path/to/payload.json
```

## Что проверить

После отправки payload:

1. **HTTP ответ должен быть 200**
   ```json
   {"status":"ok","event":"pipeline"}
   ```

2. **В Telegram должно прийти сообщение**
   - С правильным статусом (✅/❌)
   - С юмором
   - С эмодзи
   - С данными из payload

3. **В логах бота должна быть запись**
   ```
   INFO - Received GitLab webhook: pipeline
   INFO - Sent pipeline success notification
   ```

## Логи бота

```bash
# Локально (если бот запущен через uvicorn)
# Логи в stdout

# В K8s
kubectl logs -n notifications deployment/warehouse-telegram-bot --tail=100 -f
```

## Примечание

**Job Failed payload** - бот попытается получить лог через GitLab API.
Если GitLab недоступен или job не существует - отправится сообщение без лога.

## Переменные окружения для бота

Убедись что установлены:
- `TELEGRAM_BOT_TOKEN` - токен бота
- `TELEGRAM_CHAT_ID` - ID чата для уведомлений
- `GITLAB_URL` - URL GitLab (для получения логов)
- `GITLAB_TOKEN` - токен GitLab (для API)

## Troubleshooting

**403 Forbidden**
→ Проверь GITLAB_WEBHOOK_SECRET (должен быть пустым или совпадать)

**500 Internal Server Error**
→ Смотри логи бота

**Уведомления не приходят**
→ Проверь TELEGRAM_CHAT_ID и TELEGRAM_BOT_TOKEN
