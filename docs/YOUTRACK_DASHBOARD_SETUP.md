# YouTrack Dashboard Setup

**Дата**: 2025-11-29

## Что создано через API

### 1. Дашборд
- **Название**: Warehouse Project Status
- **ID**: 204-5
- **URL**: http://192.168.1.74:8088/dashboard/204-5

### 2. Сохранённые запросы (Sidebar)

| Название | Запрос | ID |
|----------|--------|-----|
| 📊 WH: Все задачи | `project: WH` | 9-7 |
| ✅ WH: Завершённые | `project: WH State: Fixed` | 9-8 |
| 🔲 WH: Открытые | `project: WH State: Submitted` | 9-9 |
| 🐛 WH: Баги | `project: WH Type: Bug State: Submitted` | 9-10 |
| 📦 WH: Эпики | `project: WH Type: Epic` | 9-11 |

---

## Настройка виджетов (через UI)

YouTrack API не позволяет добавлять виджеты программно, поэтому:

### Шаг 1: Открой дашборд
http://192.168.1.74:8088/dashboard/204-5

### Шаг 2: Добавь виджеты

Нажми **"Add widget"** и добавь:

#### Виджет 1: Issue Count (Всего задач)
- Тип: **Issue Count**
- Query: `project: WH`
- Title: Всего задач

#### Виджет 2: Issue Count (Завершено)
- Тип: **Issue Count**
- Query: `project: WH State: Fixed`
- Title: ✅ Завершено

#### Виджет 3: Issue Count (Открыто)
- Тип: **Issue Count**
- Query: `project: WH State: Submitted`
- Title: 🔲 Открыто

#### Виджет 4: Issue Distribution (По статусам)
- Тип: **Issue Distribution Report**
- Query: `project: WH`
- Group by: **State**

#### Виджет 5: Issue Distribution (По типам)
- Тип: **Issue Distribution Report**
- Query: `project: WH`
- Group by: **Type**

#### Виджет 6: Issues List (Открытые задачи)
- Тип: **Issue List**
- Saved search: 🔲 WH: Открытые

#### Виджет 7: Issues List (Баги)
- Тип: **Issue List**
- Saved search: 🐛 WH: Баги

### Шаг 3: Сделай дашборд дефолтным
- Нажми ⋮ (меню) → "Set as default"

---

## Быстрые ссылки

| Ресурс | URL |
|--------|-----|
| YouTrack | http://192.168.1.74:8088 |
| Дашборд | http://192.168.1.74:8088/dashboard/204-5 |
| Проект WH | http://192.168.1.74:8088/issues/WH |
| Все задачи | http://192.168.1.74:8088/issues?q=project:%20WH |
| Открытые | http://192.168.1.74:8088/issues?q=project:%20WH%20State:%20Submitted |

---

## Текущая статистика

```
📊 Всего задач:    28
✅ Завершено:      20
🔲 Открыто:        5
📦 Эпиков:         6
🐛 Багов:          1
```

---

## Структура эпиков

```
WH-30: CI/CD и автоматизация сборки ✅
WH-31: Интеграции с внешними системами ✅
WH-38: Инфраструктура и Kubernetes ✅
WH-39: Frontend ✅
WH-40: Backlog 🔲
WH-41: Баги 🐛
```
