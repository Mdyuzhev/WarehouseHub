---
version: 1.0.0
updated: 2025-12-03 12:00 UTC
author: claude-code
---

# Document Versioning

> Правила версионирования документации проекта Warehouse.

---

## Формат версии

Каждый документ в `docs/` содержит в шапке или заголовке версию:

```
# Document Title `v2025.12.03`
```

или YAML frontmatter:

```yaml
---
version: 1.0.0
updated: 2025-12-03 12:00 UTC
author: claude-code
---
```

---

## Когда обновлять версию

| Изменение | Действие |
|-----------|----------|
| Исправление опечаток | Обновить timestamp |
| Добавление секции | Обновить timestamp |
| Полная переработка | Новая дата в заголовке |

**Формат даты:** `v2025.12.03` или `YYYY-MM-DD HH:MM UTC`

---

## Документы для версионирования

| Файл | Текущая версия |
|------|----------------|
| ARCHITECTURE.md | v2025.12.03 |
| COMPONENTS.md | v2025.12.03 |
| INFRASTRUCTURE_GUIDE.md | v2025.12.03 |
| DEPLOY_GUIDE.md | 2025-12-01 |
| TESTING.md | (нет версии) |
| LOAD_TESTING.md | 2025-12-02 |
| TROUBLESHOOTING_GUIDE.md | 2025-12-02 |
| CREDENTIALS.md | 2025-12-01 |
| YOUTRACK_API.md | 2025-12-01 |
| PROJECT_STATUS.md | v2025.12.03 |
| RELEASE_NOTES_PROCEDURE.md | v1.0.0 |
| DOC_VERSIONING.md | v1.0.0 |

---

## Процедура обновления

1. Внести изменения в документ
2. Обновить версию/дату в шапке
3. Коммит: `docs: Update {DOC_NAME} vYYYY.MM.DD`

---

*Создано: 2025-12-03*
