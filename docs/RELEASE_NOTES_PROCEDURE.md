---
version: 1.0.0
updated: 2025-12-03 12:00 UTC
author: claude-code
---

# Release Notes Procedure

> Обязательная процедура после каждого деплоя в Production.

---

## Когда выполнять

После КАЖДОГО успешного деплоя в Production:
- namespace `warehouse` (K3s)
- Yandex Cloud (wh-lab.ru)

---

## Шаблон сообщения

Формат: HTML для Telegram

```
🚀 <b>Warehouse {EPIC_ID} — {НАЗВАНИЕ}</b>

📅 {ДАТА}

<b>Что нового:</b>
- {Фича 1 — понятным языком для пользователей}
- {Фича 2}

<b>Исправления:</b>
- {Баг 1}

📍 <i>Production: wh-lab.ru</i>
```

**Правила:**
- Писать для ПОЛЬЗОВАТЕЛЕЙ, не для разработчиков
- Избегать технического жаргона где возможно
- Не использовать символ `!` в JSON (проблема парсинга)
- Краткость — 3-5 пунктов максимум

---

## Команда отправки

```bash
# 1. Получить токен
TOKEN=$(curl -s -X POST http://192.168.1.74:30080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# 2. Отправить release notes
curl -s -X POST http://192.168.1.74:30080/api/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "TELEGRAM",
    "recipient": "-1003231635846",
    "subject": "Release Notes",
    "message": "..."
  }'
```

---

## Чеклист после деплоя

- [ ] Деплой успешен (health UP)
- [ ] Smoke test пройден
- [ ] **Release Notes отправлен в Telegram**
- [ ] Документация обновлена (с новой версией)
- [ ] Epic закрыт в YouTrack

---

*Создано: 2025-12-03*
