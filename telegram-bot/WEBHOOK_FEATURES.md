# GitLab Webhook - Добавленный функционал

## Что добавлено

### 1. Новые файлы

#### `bot/handlers/gitlab_webhook.py`
Основной handler для обработки GitLab webhooks.

**Функции:**
- `handle_gitlab_webhook(event_type, data)` - главный обработчик
- `handle_pipeline_event(data)` - обработка pipeline событий
- `handle_job_event(data)` - обработка job событий (с автоматическим получением логов при failed)

**События обрабатываются:**
- Pipeline: running, success, failed, canceled
- Job: running, success, failed, canceled

#### `GITLAB_WEBHOOK_SETUP.md`
Подробная инструкция по настройке webhooks в GitLab.

### 2. Обновлённые файлы

#### `services/gitlab.py`
Добавлена функция `get_job_trace(project_id, job_id, lines=20)` - получает последние N строк лога job через GitLab API.

#### `bot/messages.py`
Добавлены функции форматирования:
- `get_status_emoji(status)` - emoji для статуса
- `get_humor_for_status(status, event_type)` - случайная шутка для статуса
- `format_pipeline_message(data)` - форматирует сообщение о pipeline
- `format_job_message(data)` - форматирует сообщение о job
- `format_job_failed_with_log(data, log)` - форматирует сообщение о failed job с логом

#### `app.py`
Обновлён endpoint `POST /webhook/gitlab`:
- Добавлена проверка токена (опционально через `GITLAB_WEBHOOK_SECRET`)
- Делегирует обработку handler'у `handle_gitlab_webhook`
- Подробные комментарии по настройке

#### `bot/handlers/__init__.py`
Экспортирует новый handler `handle_gitlab_webhook`.

## Как это работает

### Pipeline события

```
GitLab → POST /webhook/gitlab → handle_gitlab_webhook → handle_pipeline_event → format_pipeline_message → Telegram
```

**Пример payload:**
```json
{
  "object_kind": "pipeline",
  "object_attributes": {
    "id": 123,
    "status": "success",
    "ref": "main",
    "duration": 154
  },
  "project": {
    "name": "warehouse-api"
  },
  "user": {
    "name": "Миша"
  }
}
```

**Результат в Telegram:**
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

### Job события (failed с логами)

```
GitLab → POST /webhook/gitlab → handle_gitlab_webhook → handle_job_event → get_job_trace → format_job_failed_with_log → Telegram
```

**Пример payload:**
```json
{
  "object_kind": "build",
  "build_id": 456,
  "build_name": "deploy-api-staging",
  "build_status": "failed",
  "build_stage": "deploy",
  "build_duration": 45,
  "project_id": 4,
  "project_name": "warehouse-master",
  "ref": "main",
  "user": {
    "name": "Миша"
  }
}
```

**API запрос к GitLab:**
```
GET /api/v4/projects/4/jobs/456/trace
```

**Результат в Telegram:**
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
<last 20 lines of log>

Время дебажить! 🔍
```

## Настройка в GitLab

Для каждого проекта (warehouse-master, warehouse-api, warehouse-frontend):

1. Settings → Webhooks
2. URL: `http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab`
3. Triggers: ✅ Pipeline events, ✅ Job events
4. Add webhook

## Тестирование

### Проверка синтаксиса
```bash
cd /home/flomaster/warehouse-master/telegram-bot
python3 -m py_compile app.py bot/handlers/gitlab_webhook.py bot/messages.py services/gitlab.py
```

### Ручной тест webhook
```bash
curl -X POST http://localhost:8000/webhook/gitlab \
  -H "Content-Type: application/json" \
  -d '{
    "object_kind": "pipeline",
    "object_attributes": {
      "id": 999,
      "status": "success",
      "ref": "main",
      "duration": 120,
      "url": "http://gitlab/pipelines/999"
    },
    "project": {
      "name": "test-project"
    },
    "user": {
      "name": "Test User"
    }
  }'
```

### Проверка в GitLab
1. Settings → Webhooks → Test → Pipeline events
2. Смотрим Recent Deliveries - должен быть 200 OK
3. Проверяем Telegram - должно прийти уведомление

## Переменные окружения

```bash
TELEGRAM_BOT_TOKEN="8532494921:AAEoxQ87qQVcutgCSa8d8DntT_47xhvrCAI"
TELEGRAM_CHAT_ID="290274837"
GITLAB_URL="http://192.168.1.74:8080"
GITLAB_TOKEN="glpat-Ou0qfvnfGfUOGkbs3nmv8m86MQp1OjEH.01.0w0ojabq3"
GITLAB_WEBHOOK_SECRET=""  # Опционально - для дополнительной безопасности
```

## Особенности реализации

### Юмор
Каждое сообщение содержит случайную шутку из `get_humor_for_status()`:
- Success: "Ура! Всё взлетело! 🎉", "Работает! Даже странно... 🤔"
- Failed: "Упс... Кто-то накосячил! 🙈", "ПРОВАЛ! Время смотреть логи... 📜"
- Running: "Поехали! Держитесь! 🚀", "Крутим, мутим... ⚙️"

### Логи при падении
При `build_status: failed` бот:
1. Получает `project_id` и `build_id` из webhook payload
2. Делает запрос к GitLab API: `/api/v4/projects/{project_id}/jobs/{job_id}/trace`
3. Берёт последние 20 строк лога
4. Добавляет их в сообщение с тегом `<code>`

### Фильтрация (для будущего)
В `gitlab_webhook.py` есть заглушки:
```python
def should_notify_pipeline(data: dict) -> bool:
    return True  # Пока уведомляем обо всех

def should_notify_job(data: dict) -> bool:
    return True  # Пока уведомляем обо всех
```

Можно добавить фильтры:
- По веткам (только main)
- По проектам (только production)
- По stage (только deploy)
- По имени job

## Что дальше?

Можно добавить:
1. **Фильтрация** - уведомлять только о важных событиях
2. **Группировка** - если много jobs в pipeline, сгруппировать в одно сообщение
3. **Статистика** - считать метрики (сколько failed, average duration, etc.)
4. **Кнопки** - inline кнопки "Retry job", "Cancel pipeline"
5. **Mention** - упоминать автора коммита при failed

---

**Статус:** ✅ Готово к использованию!

**Автор:** Claude Code 🤖
**Дата:** 2025-11-29
**Стиль:** С юмором, как завещал project-context.md! 🎭
