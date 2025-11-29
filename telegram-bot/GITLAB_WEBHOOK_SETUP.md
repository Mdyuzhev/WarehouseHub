# GitLab Webhook Setup - Настройка уведомлений

Этот гайд поможет настроить автоматические уведомления о pipeline и job событиях из GitLab в Telegram.

## Что получишь

После настройки бот будет присылать уведомления:
- **Pipeline события**: старт, успех, провал
- **Job события**: старт, успех, провал (с логами при падении!)

Всё с юмором, эмодзи и ссылками на GitLab! 🚀

## Настройка webhook в GitLab

Нужно настроить для **каждого** проекта:
- warehouse-master
- warehouse-api
- warehouse-frontend

### Шаги

1. Открой проект в GitLab: http://192.168.1.74:8080
2. Иди в **Settings → Webhooks**
3. Добавь новый webhook:

#### URL
```
http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab
```

**Важно**: Это внутренний K8s DNS! Если бот работает вне кластера - используй внешний URL.

#### Secret Token (опционально)
Можно оставить пустым или указать токен из переменной окружения `GITLAB_WEBHOOK_SECRET`.

#### Triggers (галочки)

Обязательно включи:
- ✅ **Pipeline events** - события pipeline (started, success, failed)
- ✅ **Job events** - события job (started, success, failed)

Остальные можно отключить (Push events, Tag events и т.д.).

#### SSL verification
Если бот внутри K8s с self-signed сертификатом - отключи "Enable SSL verification".

4. Жми **Add webhook**
5. Проверь webhook кнопкой **Test → Pipeline events**

Если всё ок - в Telegram придёт уведомление! 🎉

## Что приходит в сообщениях

### Pipeline события

```
✅ Pipeline SUCCESS

📦 Проект: warehouse-api
🌿 Ветка: main
🆔 Pipeline: #123
👤 Автор: Миша
⏱ Время: 2м 34с

Ура! Всё взлетело! 🎉

🔗 Открыть в GitLab
```

### Job события (успех)

```
✅ Job SUCCESS: deploy-api-staging

📦 Проект: warehouse-master
🌿 Ветка: main
🏗 Stage: deploy
🆔 Job ID: #456
👤 Автор: Миша
⏱ Время: 1м 12с

Работает! Даже странно... 🤔
```

### Job события (провал с логами!)

```
❌ Job FAILED: deploy-api-staging

📦 Проект: warehouse-master
🌿 Ветка: main
🏗 Stage: deploy
🆔 Job ID: #456
👤 Автор: Миша
⏱ Время: 0м 45с

Упс... Кто-то накосячил! 🙈

📜 Лог (последние строки):
ERROR: Failed to connect to database
Connection refused
...

Время дебажить! 🔍
```

## Проверка работы

### 1. Проверь что бот запущен

```bash
kubectl get pods -n notifications
```

Должен быть pod `warehouse-telegram-bot-xxx` в статусе `Running`.

### 2. Проверь логи бота

```bash
kubectl logs -n notifications deployment/warehouse-telegram-bot --tail=100 -f
```

При получении webhook должны появиться логи:
```
INFO - Received GitLab webhook: pipeline
INFO - Sent pipeline success notification
```

### 3. Тестовый webhook

В GitLab:
1. Settings → Webhooks
2. Найди созданный webhook
3. Нажми **Test → Pipeline events**

В Telegram должно прийти уведомление!

### 4. Реальная проверка

Запусти любой pipeline в GitLab и следи за уведомлениями в Telegram! 🚀

## Troubleshooting

### Webhook не работает

1. **Проверь URL**:
   ```bash
   kubectl get svc -n notifications
   ```
   Убедись что service `warehouse-telegram-bot` существует.

2. **Проверь что бот доступен**:
   ```bash
   kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
     curl http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/health
   ```

3. **Проверь Recent Deliveries** в GitLab:
   - Settings → Webhooks → Edit → Recent Deliveries
   - Смотри статус код и response body

### Уведомления не приходят в Telegram

1. **Проверь TELEGRAM_CHAT_ID** в переменных окружения
2. **Проверь TELEGRAM_BOT_TOKEN**
3. **Смотри логи бота** - там будут ошибки если есть

### Логи не приходят при failed job

Проверь что:
- У бота есть **GITLAB_TOKEN** с правами на чтение jobs
- Token имеет scope `api` или `read_api`

## Переменные окружения бота

```yaml
TELEGRAM_BOT_TOKEN: "8532494921:AAEoxQ87qQVcutgCSa8d8DntT_47xhvrCAI"
TELEGRAM_CHAT_ID: "290274837"
GITLAB_URL: "http://192.168.1.74:8080"
GITLAB_TOKEN: "glpat-Ou0qfvnfGfUOGkbs3nmv8m86MQp1OjEH.01.0w0ojabq3"
GITLAB_WEBHOOK_SECRET: ""  # Опционально
```

## Фичи

- 🎭 **Юмор** - каждое сообщение с шуткой (в стиле проекта!)
- 🎨 **Эмодзи** - красиво и понятно
- 📜 **Логи** - при failed job автоматически подтягиваются последние 20 строк лога
- 🔗 **Ссылки** - каждое сообщение со ссылкой на GitLab
- ⚡ **Быстро** - async обработка webhooks

## Расширение

Хочешь фильтровать события? Редактируй функции в `bot/handlers/gitlab_webhook.py`:

```python
def should_notify_pipeline(data: dict) -> bool:
    # Например, только main ветка
    ref = data.get("object_attributes", {}).get("ref")
    return ref == "main"

def should_notify_job(data: dict) -> bool:
    # Например, только deploy jobs
    job_name = data.get("build_name", "")
    return "deploy" in job_name
```

---

**Готово!** Теперь ты будешь в курсе всего что происходит в CI/CD! 🎉

*P.S. Если что-то не работает - зови меня (Claude), разберёмся! 🤖*
