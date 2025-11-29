# GitLab Webhook Integration - Полное руководство

## Оглавление

- [Быстрый старт](#быстрый-старт)
- [Что добавлено](#что-добавлено)
- [Файловая структура](#файловая-структура)
- [Настройка в GitLab](#настройка-в-gitlab)
- [Тестирование](#тестирование)
- [Примеры сообщений](#примеры-сообщений)
- [Troubleshooting](#troubleshooting)

---

## Быстрый старт

### 1. Проверь что бот запущен
```bash
kubectl get pods -n notifications | grep telegram-bot
```

### 2. Настрой webhook в GitLab
Для каждого проекта (warehouse-master, warehouse-api, warehouse-frontend):

- **URL:** `http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab`
- **Triggers:** ✅ Pipeline events, ✅ Job events
- **Secret:** оставь пустым

### 3. Протестируй
Settings → Webhooks → Test → Pipeline events

Должно прийти уведомление в Telegram! 🎉

**Подробнее:** смотри [QUICK_START_WEBHOOK.md](QUICK_START_WEBHOOK.md)

---

## Что добавлено

### Функционал

✅ **Pipeline уведомления:**
- Started (running)
- Success
- Failed
- Canceled

✅ **Job уведомления:**
- Started (running)
- Success
- Failed (+ последние 20 строк лога!)
- Canceled

✅ **Особенности:**
- Юмор в каждом сообщении
- Эмодзи для статусов
- Ссылки на GitLab
- Автоматическое получение логов при failed jobs
- Форматирование HTML
- Длительность выполнения

### Технические детали

- **Endpoint:** `POST /webhook/gitlab`
- **Формат:** JSON (GitLab webhook payload)
- **Авторизация:** опциональный токен через `GITLAB_WEBHOOK_SECRET`
- **Async обработка:** быстро и эффективно

---

## Файловая структура

```
telegram-bot/
├── bot/
│   ├── handlers/
│   │   ├── gitlab_webhook.py       ← Обработчик webhooks (НОВОЕ)
│   │   ├── commands.py
│   │   ├── deploy.py
│   │   ├── testing.py
│   │   └── claude.py
│   ├── messages.py                 ← Форматирование (ОБНОВЛЕНО +181 строка)
│   ├── telegram.py
│   └── keyboards.py
├── services/
│   ├── gitlab.py                   ← get_job_trace() (ОБНОВЛЕНО +38 строк)
│   ├── health.py
│   ├── locust.py
│   └── allure.py
├── test_payloads/                  ← Тестовые данные (НОВОЕ)
│   ├── pipeline_success.json
│   ├── pipeline_failed.json
│   ├── job_success.json
│   ├── job_failed.json
│   └── README.md
├── app.py                          ← Endpoint (ОБНОВЛЕНО)
├── config.py
├── test_webhook.sh                 ← Скрипт для тестирования (НОВОЕ)
├── QUICK_START_WEBHOOK.md          ← Быстрый старт (НОВОЕ)
├── GITLAB_WEBHOOK_SETUP.md         ← Подробная настройка (НОВОЕ)
├── WEBHOOK_FEATURES.md             ← Техдокументация (НОВОЕ)
└── WEBHOOK_GITLAB_CONFIG.txt       ← Конфигурация GitLab (НОВОЕ)
```

---

## Настройка в GitLab

### Шаги

1. Открой проект в GitLab
2. Settings → Webhooks
3. Заполни форму:

   **URL:**
   ```
   http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab
   ```

   **Triggers:**
   - ✅ Pipeline events
   - ✅ Job events

   **SSL verification:**
   - ☐ Отключено (внутри K8s используется HTTP)

4. Add webhook
5. Test → Pipeline events

### Проекты для настройки

- [ ] warehouse-master
- [ ] warehouse-api
- [ ] warehouse-frontend

**Подробная инструкция:** [GITLAB_WEBHOOK_SETUP.md](GITLAB_WEBHOOK_SETUP.md)

---

## Тестирование

### Вариант 1: Скрипт (рекомендуется)

```bash
cd /home/flomaster/warehouse-master/telegram-bot
./test_webhook.sh
```

Выбери нужный тест из меню.

### Вариант 2: Curl вручную

```bash
# Pipeline Success
curl -X POST http://localhost:8000/webhook/gitlab \
  -H "Content-Type: application/json" \
  -d @test_payloads/pipeline_success.json

# Job Failed (с логами)
curl -X POST http://localhost:8000/webhook/gitlab \
  -H "Content-Type: application/json" \
  -d @test_payloads/job_failed.json
```

### Вариант 3: Из GitLab

Settings → Webhooks → Test → Pipeline events

---

## Примеры сообщений

### Pipeline Success

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

### Job Failed (с логом!)

```
❌ Job FAILED: deploy-frontend-prod

📦 Проект: warehouse-master
🌿 Ветка: main
🏗 Stage: deploy
🆔 Job ID: #457
👤 Автор: Миша
⏱ Время: 0м 45с

Упс... Кто-то накосячил! 🙈

📜 Лог (последние строки):
ERROR: Connection to database failed
FATAL: Unable to connect to host
...

Время дебажить! 🔍
```

---

## Troubleshooting

### Webhook не работает

**Проблема:** HTTP 403 Forbidden
```bash
# Проверь GITLAB_WEBHOOK_SECRET
kubectl get secret -n notifications warehouse-telegram-bot-secret -o yaml
```

**Проблема:** Connection refused
```bash
# Проверь что бот запущен
kubectl get pods -n notifications

# Проверь service
kubectl get svc -n notifications warehouse-telegram-bot
```

**Проблема:** 500 Internal Server Error
```bash
# Смотри логи бота
kubectl logs -n notifications deployment/warehouse-telegram-bot --tail=100
```

### Уведомления не приходят

**Проверь переменные окружения:**
```bash
kubectl get deployment -n notifications warehouse-telegram-bot -o yaml | grep -A 20 env:
```

Должны быть:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `GITLAB_URL`
- `GITLAB_TOKEN`

### Логи не приходят при failed job

**Проверь GitLab токен:**
```bash
# Токен должен иметь scope: api или read_api
echo $GITLAB_TOKEN
```

**Тестовый запрос:**
```bash
curl -H "PRIVATE-TOKEN: your-token" \
  http://192.168.1.74:8080/api/v4/projects/4/jobs/123/trace
```

---

## Переменные окружения

```yaml
TELEGRAM_BOT_TOKEN: "8532494921:AAEoxQ87qQVcutgCSa8d8DntT_47xhvrCAI"
TELEGRAM_CHAT_ID: "290274837"
GITLAB_URL: "http://192.168.1.74:8080"
GITLAB_TOKEN: "glpat-Ou0qfvnfGfUOGkbs3nmv8m86MQp1OjEH.01.0w0ojabq3"
GITLAB_WEBHOOK_SECRET: ""  # Опционально
```

---

## Полезные команды

```bash
# Логи бота
kubectl logs -n notifications deployment/warehouse-telegram-bot --tail=100 -f

# Перезапуск бота
kubectl rollout restart deployment/warehouse-telegram-bot -n notifications

# Проверка endpoints
kubectl get endpoints -n notifications warehouse-telegram-bot

# Тест доступности изнутри K8s
kubectl run -it --rm test --image=curlimages/curl --restart=Never -- \
  curl http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/health
```

---

## Дополнительная документация

- **[QUICK_START_WEBHOOK.md](QUICK_START_WEBHOOK.md)** - Быстрый старт за 2 минуты
- **[GITLAB_WEBHOOK_SETUP.md](GITLAB_WEBHOOK_SETUP.md)** - Подробная настройка webhook
- **[WEBHOOK_FEATURES.md](WEBHOOK_FEATURES.md)** - Технические детали и архитектура
- **[WEBHOOK_GITLAB_CONFIG.txt](WEBHOOK_GITLAB_CONFIG.txt)** - Визуальный гайд по настройке в GitLab
- **[test_payloads/README.md](test_payloads/README.md)** - Инструкция по тестированию

---

## Что дальше?

Можно расширить функционал:

1. **Фильтрация** - уведомлять только о важных событиях
2. **Статистика** - считать метрики (failed rate, average duration)
3. **Кнопки** - добавить inline кнопки "Retry", "Cancel"
4. **Mention** - упоминать автора при failed
5. **Группировка** - объединять события одного pipeline

---

**Готово!** Теперь ты в курсе всего что происходит в CI/CD! 🚀

**Сделано с юмором by Claude Code** 🤖
