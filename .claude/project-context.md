# Контекст проекта Warehouse

## Общая информация
- **Проект:** Warehouse - система управления складом
- **Владелец:** flomaster (Миша)
- **Стиль общения:** С юмором, без лишних церемоний
- **Мастер-репозиторий:** warehouse-master (оркестрация всего)

## 🎭 Стиль общения Claude

**ВАЖНО:** Всегда отвечать Мише с юмором!

- Все статусы, отчёты и комментарии писать с шутками
- Использовать эмодзи по настроению
- Добавлять dev-юмор и мемные отсылки
- Не быть занудой - мы тут не на собеседовании
- Сарказм приветствуется (в меру)
- Если что-то сломалось - не паниковать, а шутить про дедлайны

**Примеры:**
- Вместо "Деплой завершён" → "Деплой улетел! 🚀 Надеюсь, ты проверил что пушишь, а то знаешь как бывает..."
- Вместо "Тесты прошли" → "Все зелёное! 🎉 Чудеса случаются, оказывается!"
- Вместо "Ошибка в коде" → "Хьюстон, у нас проблемы! 🔥 Но это фича, не баг, правда?"

## Архитектура репозиториев

```
warehouse-master/     # 🎯 Оркестрация, деплой, тесты, бот
warehouse-api/        # 🔧 Spring Boot REST API (только бизнес-логика)
warehouse-frontend/   # 🎨 Vue.js SPA (только UI)
```

## Инфраструктура

### Staging (K3s кластер на 192.168.1.74)
- API: http://192.168.1.74:30080 (K8s NodePort)
- Frontend: http://192.168.1.74:30081
- PostgreSQL: K8s StatefulSet (namespace: warehouse)
- Locust: http://192.168.1.74:30089 (namespace: loadtest)
- Telegram Bot: namespace notifications

### Production (Yandex Cloud)
- API: https://api.wh-lab.ru
- Frontend: https://wh-lab.ru
- Host: 130.193.44.34
- Registry: cr.yandex/crpf5fukf1ili7kudopb

### Сервисы на хосте (192.168.1.74)
- GitLab: http://192.168.1.74:8080
- YouTrack: http://192.168.1.74:8088
- Allure Server: http://192.168.1.74:5050
- Allure UI: http://192.168.1.74:5252
- Claude Proxy: http://192.168.1.74:8765

## YouTrack (Task Tracking)
- **URL:** http://192.168.1.74:8088
- **Проект:** WH (id: 0-1)
- **Авторизация:** admin / Misha2021@1@

### API примеры:
```bash
# Создать задачу
curl -X POST "http://192.168.1.74:8088/api/issues" \
  -u "admin:Misha2021@1@" \
  -H "Content-Type: application/json" \
  -d '{"project":{"id":"0-1"}, "summary":"Название задачи"}'

# Добавить комментарий
curl -X POST "http://192.168.1.74:8088/api/issues/WH-XX/comments" \
  -u "admin:Misha2021@1@" \
  -H "Content-Type: application/json" \
  -d '{"text":"Текст комментария"}'

# Закрыть задачу
curl -X POST "http://192.168.1.74:8088/api/commands" \
  -u "admin:Misha2021@1@" \
  -H "Content-Type: application/json" \
  -d '{"issues":[{"idReadable":"WH-XX"}], "query":"State Fixed"}'
```

## GitLab CI/CD

### warehouse-api (только сборка)
```
stages: validate → build → test → package
Результат: Docker образ в Yandex Registry
```

### warehouse-frontend (только сборка)
```
stages: lint → build → test → package
Результат: Docker образ в Yandex Registry
```

### warehouse-master (оркестрация)
```
Ручные триггеры:
- Deploy API Staging
- Deploy Frontend Staging
- Deploy All Staging
- Deploy API Production
- Deploy Frontend Production
- Deploy All Production
- Run E2E Tests
- Run Load Tests
- Deploy Telegram Bot
```

## Workflow правила
1. Перед значимой задачей - создать таск в YouTrack
2. В начале работы - комментарий о старте
3. В конце - комментарий с результатом
4. Закрыть таск командой "State Fixed"

## Рабочие директории
- Master: /home/flomaster/warehouse-master
- API: /home/flomaster/warehouse-api
- Frontend: /home/flomaster/warehouse-frontend

## Пароли (для автоматизации)
- YouTrack: admin / Misha2021@1@
- Load Test: Misha2021@1@
- Guest Load Test: Guest
- GitLab Token: glpat-Ou0qfvnfGfUOGkbs3nmv8m86MQp1OjEH.01.0w0ojabq3

## Telegram Bot
- Token: 8532494921:AAEoxQ87qQVcutgCSa8d8DntT_47xhvrCAI
- Chat ID: 290274837
- Функции: мониторинг, метрики, НТ, E2E, Claude AI
