# Инструкция: Старт работы

## Описание
Загрузка полного контекста проекта Warehouse для начала работы.

## Когда запускать
- В начале каждой новой сессии
- После длительного перерыва
- Когда нужно освежить контекст

---

## Команда для запуска

```
Старт
```

или

```
Запусти инструкцию start
```

---

## Шаги выполнения

### 1. Прочитать основные документы

Обязательно прочитать следующие файлы:

| Документ | Описание |
|----------|----------|
| `.claude/settings.local.json` | Настройки проекта, workflow, критичные напоминания |
| `docs/CREDENTIALS.md` | Все секреты, учётки, пароли |
| `docs/ARCHITECTURE.md` | Высокоуровневая архитектура |
| `docs/COMPONENTS.md` | Компоненты, порты, технологии |
| `docs/INFRASTRUCTURE_GUIDE.md` | K8s namespaces, сервисы |
| `docs/DEPLOY_GUIDE.md` | Процедуры деплоя |
| `docs/TESTING.md` | Тестирование, учётки, endpoints |
| `docs/YOUTRACK_API.md` | YouTrack API референс |
| `docs/TROUBLESHOOTING_GUIDE.md` | Типичные проблемы и решения |

### 2. Проверить статус окружений

```bash
# Staging health
curl -s http://192.168.1.74:30080/actuator/health | jq -r '.status'

# Production health
curl -s https://api.wh-lab.ru/actuator/health | jq -r '.status'

# Git status
cd /home/flomaster/warehouse-master && git status
```

### 3. Вывести краткую справку

После изучения документов вывести справку по формату:

```markdown
## Краткая справка по сетапу

**Сервер:** 192.168.1.74 (staging) | 130.193.44.34 (prod)

**Основные сервисы:**
| Сервис | Порт | Статус |
|--------|------|--------|
| Warehouse API | 30080 | UP/DOWN |
| Frontend | 30081 | UP/DOWN |
| Robot | 30070 | UP/DOWN |
| Analytics | 30091 | UP/DOWN |
| Telegram Bot | 30088 | UP/DOWN |

**K8s namespaces:** warehouse, warehouse-dev, notifications, loadtest, monitoring

**Критичные напоминания:**
- K3s использует containerd, НЕ Docker!
- YouTrack: ТОЛЬКО Basic Auth
- Деплой: 7 шагов обязательно (см. DEPLOY_GUIDE.md)
- НЕ пушить напрямую в main!

**Production:**
- API: https://api.wh-lab.ru
- Frontend: https://wh-lab.ru

Готов к задаче!
```

---

## Примечания

- Документы читаются параллельно для ускорения
- Health check может быть недоступен если сервер выключен
- После справки можно сразу приступать к задаче

