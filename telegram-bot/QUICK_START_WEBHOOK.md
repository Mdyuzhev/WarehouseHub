# GitLab Webhook - Quick Start

## TL;DR - Быстрый старт

### Что делает
Бот присылает уведомления в Telegram:
- Pipeline started/success/failed
- Job started/success/failed (при failed - с логами!)
- Всё с юмором и эмодзи 🚀

### Настройка за 2 минуты

1. **Проверь что бот запущен:**
   ```bash
   kubectl get pods -n notifications | grep telegram-bot
   ```

2. **Добавь webhook в GitLab** (для каждого проекта):

   - URL: `http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab`
   - Triggers: ✅ Pipeline events, ✅ Job events
   - Secret: оставь пустым

3. **Тест:**

   Settings → Webhooks → Test → Pipeline events

   В Telegram должно прийти сообщение! 🎉

### Что будет приходить

**Pipeline success:**
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

**Job failed (с логами!):**
```
❌ Job FAILED: deploy-api-staging
📦 Проект: warehouse-master
🌿 Ветка: main
🏗 Stage: deploy
🆔 Job ID: #456
👤 Автор: Миша

Упс... Кто-то накосячил! 🙈

📜 Лог (последние строки):
ERROR: Connection refused
...

Время дебажить! 🔍
```

### Проекты для настройки
- [ ] warehouse-master
- [ ] warehouse-api
- [ ] warehouse-frontend

### Troubleshooting

**Webhook не работает?**
```bash
# Проверь логи бота
kubectl logs -n notifications deployment/warehouse-telegram-bot --tail=50
```

**Уведомления не приходят?**
Проверь переменные окружения:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `GITLAB_TOKEN`

### Подробности
Смотри полную документацию в:
- `GITLAB_WEBHOOK_SETUP.md` - настройка
- `WEBHOOK_FEATURES.md` - технические детали

---

**Всё готово!** Теперь будешь в курсе всего что творится в CI/CD! 🎯
