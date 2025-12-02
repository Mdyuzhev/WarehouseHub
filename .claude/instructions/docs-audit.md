# Инструкция: Полная ревизия документации

## Описание
Проведение полной ревизии всех репозиториев проекта и обновление документации по итогам крупных изменений.

## Когда запускать
- После завершения User Story или Epic
- После значительных архитектурных изменений
- Периодически (раз в неделю/месяц)

---

## Команда для запуска

```
Запусти инструкцию docs-audit из .claude/instructions/docs-audit.md
```

---

## Шаги выполнения

### 1. Подготовка

Прочитать настройки проекта:
- `/home/flomaster/warehouse-master/.claude/settings.local.json`

### 2. Ревизия репозиториев

Провести аудит всех трёх репозиториев:

| Репозиторий | Путь | Что проверять |
|-------------|------|---------------|
| warehouse-api | `/home/flomaster/warehouse-api` | pom.xml, структура, endpoints, конфиги |
| warehouse-frontend | `/home/flomaster/warehouse-frontend` | package.json, компоненты, роуты |
| warehouse-master | `/home/flomaster/warehouse-master` | K8s манифесты, сервисы, скрипты |

**Проверить:**
- Версии зависимостей
- Новые/удалённые файлы
- Изменения в API endpoints
- Изменения в K8s манифестах
- Актуальность портов и сервисов

### 3. Проверка Production

```bash
# Health check prod
curl -s https://api.wh-lab.ru/actuator/health | jq

# Проверить контейнеры
ssh -i ~/.ssh/yc_prod_key ubuntu@130.193.44.34 'cd /opt/warehouse && sudo docker compose ps'
```

### 4. Проверка Staging

```bash
# Health check staging
curl -s http://192.168.1.74:30080/actuator/health | jq

# Проверить pods
kubectl get pods -A | grep -E "warehouse|notification|loadtest|monitoring"
```

### 5. Обновление документации

Обновить следующие документы на основе результатов ревизии:

| Документ | Что обновлять |
|----------|---------------|
| `docs/ARCHITECTURE.md` | Высокоуровневая архитектура, диаграммы, связи |
| `docs/COMPONENTS.md` | Компоненты, порты, версии, технологии |
| `docs/INFRASTRUCTURE_GUIDE.md` | K8s namespaces, сервисы, NodePorts |
| `docs/DEPLOY_GUIDE.md` | Процедуры деплоя, команды |
| `docs/TROUBLESHOOTING_GUIDE.md` | Новые проблемы и решения |
| `docs/TESTING.md` | Тестовые учётки, endpoints |

### 6. Обновление settings.local.json

Обновить в `.claude/settings.local.json`:
- `audit.last_audit` - текущая дата
- `audit.last_user_story` - последняя завершённая задача

---

## Формат отчёта

По завершении предоставить отчёт:

```markdown
## Отчёт по ревизии документации

**Дата:** YYYY-MM-DD
**Последняя задача:** WH-XXX

### Проверено

| Компонент | Статус | Изменения |
|-----------|--------|-----------|
| warehouse-api | OK/UPDATED | описание |
| warehouse-frontend | OK/UPDATED | описание |
| warehouse-master | OK/UPDATED | описание |
| Production | UP/DOWN | описание |
| Staging | UP/DOWN | описание |

### Обновлённые документы

- [ ] ARCHITECTURE.md - что изменено
- [ ] COMPONENTS.md - что изменено
- [ ] INFRASTRUCTURE_GUIDE.md - что изменено
- [ ] DEPLOY_GUIDE.md - что изменено
- [ ] TROUBLESHOOTING_GUIDE.md - что изменено

### Найденные проблемы

1. Проблема 1 - статус
2. Проблема 2 - статус

### Рекомендации

- Рекомендация 1
- Рекомендация 2
```

---

## Примечания

- НЕ запускать инструкцию автоматически - только по запросу
- Перед обновлением документов сделать `git pull`
- После обновления НЕ коммитить автоматически - дождаться подтверждения
