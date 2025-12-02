# YouTrack API Reference

> Справочник по работе с YouTrack API для проекта Warehouse. Обновлено: 2025-12-01

---

## ⚠️ КРИТИЧЕСКИ ВАЖНО: Только Basic Auth!

```
OAuth НЕ работает!
/api/users/login НЕ работает!
Использовать ТОЛЬКО Basic Auth: -u 'admin:Misha2021@1@'
```

---

## Базовые параметры

| Параметр | Значение |
|----------|----------|
| URL | http://192.168.1.74:8088 |
| User | admin |
| Password | Misha2021@1@ |
| Project ID | 0-1 |
| Project Short | WH |

---

## Быстрые команды

```bash
# Получить задачу
curl -s -u 'admin:Misha2021@1@' 'http://192.168.1.74:8088/api/issues/WH-120'

# Создать задачу
curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/issues?fields=id,idReadable,summary' \
  -H 'Content-Type: application/json' \
  -d '{"project":{"id":"0-1"},"summary":"Название задачи"}'

# Добавить комментарий
curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/issues/WH-120/comments' \
  -H 'Content-Type: application/json' \
  -d '{"text":"Текст комментария"}'
```

---

## ID полей (Custom Fields)

### Type (Тип задачи)

| Field ID | `162-8` |
|----------|---------|

| Тип | Value ID |
|-----|----------|
| User Story | `143-15` |
| Bug | `143-5` |
| Task | `143-9` |
| Epic | `143-12` |
| Feature | `143-8` |

### State (Статус)

| Field ID | `162-9` |
|----------|---------|

| Статус | Value ID |
|--------|----------|
| Submitted | `145-0` |
| In Progress | `145-1` |
| Fixed | `145-7` |

### Priority (Приоритет)

| Field ID | `162-7` |
|----------|---------|

| Приоритет | Value ID |
|-----------|----------|
| Normal | `143-3` |
| Major | `143-2` |

---

## Типы связей

| Связь | ID | Source → Target | Target → Source |
|-------|-----|-----------------|-----------------|
| Subtask | `152-3` | parent for | subtask of |

---

## User Story Workflow

Полный цикл создания User Story с подзадачами.

### Шаг 1: Изменить тип на User Story

```bash
curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/issues/WH-XXX' \
  -H 'Content-Type: application/json' \
  -d '{"customFields":[{"name":"Type","$type":"SingleEnumIssueCustomField","value":{"id":"143-15"}}]}'
```

### Шаг 2: Обновить описание

> ⚠️ Для кириллицы использовать файл и charset=utf-8

```bash
# Создать файл с описанием
cat > /tmp/description.json << 'EOF'
{
  "description": "## Цель\nОписание цели\n\n## Функциональность\n- Пункт 1\n- Пункт 2"
}
EOF

# Применить описание
curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/issues/WH-XXX' \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d @/tmp/description.json
```

### Шаг 3: Изменить статус на Fixed

```bash
curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/issues/WH-XXX' \
  -H 'Content-Type: application/json' \
  -d '{"customFields":[{"name":"State","$type":"StateIssueCustomField","value":{"id":"145-7"}}]}'
```

### Шаг 4: Создать подзадачу

```bash
curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/issues?fields=id,idReadable' \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d '{"project":{"id":"0-1"},"summary":"Название подзадачи"}'
```

### Шаг 5: Связать подзадачу с родителем

> Команда `subtask of` применяется к подзадаче — родитель получит связь `parent for`

```bash
curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/commands' \
  -H 'Content-Type: application/json' \
  -d '{"issues": [{"idReadable": "WH-YYY"}], "query": "subtask of WH-XXX"}'
```

### Шаг 6: Установить статус подзадачи Fixed

```bash
curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/issues/WH-YYY' \
  -H 'Content-Type: application/json' \
  -d '{"customFields":[{"name":"State","$type":"StateIssueCustomField","value":{"id":"145-7"}}]}'
```

### Шаг 7: Добавить трудозатраты

> minutes — время в минутах, date — timestamp в миллисекундах

```bash
# Получить timestamp
TIMESTAMP_MS=$(date +%s)000

curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/issues/WH-YYY/timeTracking/workItems' \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d "{\"duration\":{\"minutes\":120},\"text\":\"Описание работы\",\"date\":$TIMESTAMP_MS}"
```

---

## Формат описания User Story

```markdown
## Цель
Краткое описание цели

## Описание
Подробное описание задачи

## Функциональность
- Функция 1
- Функция 2
- Функция 3

## Архитектура
```
Схема или описание архитектуры
```

## Критерии готовности
- [x] Критерий 1
- [x] Критерий 2
- [ ] Критерий 3
```

---

## Решение проблем

### Кириллица ломается в JSON

```bash
# Неправильно
curl ... -d '{"summary":"Кириллица"}'

# Правильно — через файл
echo '{"summary":"Кириллица"}' > /tmp/data.json
curl ... -H 'Content-Type: application/json; charset=utf-8' -d @/tmp/data.json

# Или через HEREDOC
curl ... -H 'Content-Type: application/json; charset=utf-8' -d "$(cat <<'EOF'
{"summary":"Кириллица работает"}
EOF
)"
```

### 401 Unauthorized

```bash
# Проверь что используешь Basic Auth
curl -s -u 'admin:Misha2021@1@' 'http://192.168.1.74:8088/api/issues/WH-1'

# НЕ используй Bearer токены — они не работают!
```

### 404 Not Found

```bash
# Проверь ID проекта
curl -s -u 'admin:Misha2021@1@' 'http://192.168.1.74:8088/api/admin/projects'

# Проверь существование задачи
curl -s -u 'admin:Misha2021@1@' 'http://192.168.1.74:8088/api/issues?query=project:WH'
```

---

## Полезные запросы

```bash
# Все задачи проекта
curl -s -u 'admin:Misha2021@1@' \
  'http://192.168.1.74:8088/api/issues?query=project:WH&fields=idReadable,summary,customFields(name,value(name))'

# Задачи в статусе In Progress
curl -s -u 'admin:Misha2021@1@' \
  'http://192.168.1.74:8088/api/issues?query=project:WH%20State:In%20Progress'

# Подзадачи родителя
curl -s -u 'admin:Misha2021@1@' \
  'http://192.168.1.74:8088/api/issues/WH-103/links?fields=direction,linkType(name),issues(idReadable,summary)'

# Все типы связей
curl -s -u 'admin:Misha2021@1@' \
  'http://192.168.1.74:8088/api/issueLinkTypes'

# Все поля проекта
curl -s -u 'admin:Misha2021@1@' \
  'http://192.168.1.74:8088/api/admin/projects/0-1/customFields?fields=id,field(name),bundle(values(id,name))'
```

---

*Последнее обновление: 2025-12-01*
