# Чеклист для запуска GitLab Webhook уведомлений

## Предварительная проверка

- [ ] Бот задеплоен в K8s namespace `notifications`
- [ ] Service `warehouse-telegram-bot` существует и доступен
- [ ] Переменные окружения бота настроены (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GITLAB_TOKEN)

## Настройка webhook в GitLab

### Проект: warehouse-master

- [ ] Открыл http://192.168.1.74:8080/root/warehouse-master
- [ ] Settings → Webhooks
- [ ] Добавил URL: `http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab`
- [ ] Включил triggers: Pipeline events, Job events
- [ ] Сохранил webhook
- [ ] Протестировал: Test → Pipeline events
- [ ] Получил уведомление в Telegram

### Проект: warehouse-api

- [ ] Открыл http://192.168.1.74:8080/root/warehouse-api
- [ ] Settings → Webhooks
- [ ] Добавил URL: `http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab`
- [ ] Включил triggers: Pipeline events, Job events
- [ ] Сохранил webhook
- [ ] Протестировал: Test → Pipeline events
- [ ] Получил уведомление в Telegram

### Проект: warehouse-frontend

- [ ] Открыл http://192.168.1.74:8080/root/warehouse-frontend
- [ ] Settings → Webhooks
- [ ] Добавил URL: `http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab`
- [ ] Включил triggers: Pipeline events, Job events
- [ ] Сохранил webhook
- [ ] Протестировал: Test → Pipeline events
- [ ] Получил уведомление в Telegram

## Проверка работы

- [ ] Запустил реальный pipeline в одном из проектов
- [ ] Получил уведомление о старте pipeline
- [ ] Получил уведомления о job'ах (started)
- [ ] Получил уведомление об успехе/провале pipeline
- [ ] Получил уведомления об успехе/провале job'ов
- [ ] При failed job пришли логи (последние 20 строк)

## Тестирование локально (опционально)

- [ ] Запустил `./test_webhook.sh`
- [ ] Протестировал все типы событий:
  - [ ] Pipeline Success
  - [ ] Pipeline Failed
  - [ ] Job Success
  - [ ] Job Failed
- [ ] Все тесты прошли успешно (HTTP 200)
- [ ] Уведомления пришли в Telegram

## Проверка логов

- [ ] Проверил логи бота: `kubectl logs -n notifications deployment/warehouse-telegram-bot --tail=100`
- [ ] В логах видны записи о получении webhooks:
  - `INFO - Received GitLab webhook: pipeline`
  - `INFO - Sent pipeline success notification`
  - `INFO - Received GitLab webhook: build`
  - `INFO - Sent job failed notification`
- [ ] Нет ошибок в логах

## Дополнительно

- [ ] Прочитал README_WEBHOOK.md
- [ ] Прочитал QUICK_START_WEBHOOK.md
- [ ] Знаю где смотреть подробную документацию (GITLAB_WEBHOOK_SETUP.md, WEBHOOK_FEATURES.md)
- [ ] Знаю как дебажить (смотреть логи, проверять Recent Deliveries в GitLab)

## Готово! 🎉

Если все чекбоксы отмечены - интеграция работает!

Теперь ты будешь получать уведомления о всех событиях в CI/CD прямо в Telegram с юмором и эмодзи! 🚀

---

**Что-то не работает?**

1. Смотри логи бота: `kubectl logs -n notifications deployment/warehouse-telegram-bot --tail=100`
2. Проверь Recent Deliveries в GitLab (Settings → Webhooks → Edit → Recent Deliveries)
3. Читай раздел Troubleshooting в README_WEBHOOK.md
4. Пиши мне (Claude)! 🤖
