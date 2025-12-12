# Warehouse Documentation

Документация проекта Warehouse Management System.

---

## Быстрые ссылки

| Документ | Описание |
|----------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Архитектура системы, компоненты, схемы |
| [COMPONENTS.md](COMPONENTS.md) | Детали компонентов, порты, технологии |
| [TASK_TEMPLATE.md](TASK_TEMPLATE.md) | Как правильно ставить задачи |

---

## Руководства

| Документ | Описание |
|----------|----------|
| [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) | Процедуры деплоя |
| [INFRASTRUCTURE_GUIDE.md](INFRASTRUCTURE_GUIDE.md) | K8s, namespaces, сервисы |
| [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) | Решение проблем |
| [LOAD_TESTING.md](LOAD_TESTING.md) | Нагрузочное тестирование |

---

## Тестирование

| Документ | Расположение | Описание |
|----------|--------------|----------|
| E2E Testing Guide | [/testing/TESTING.md](/testing/TESTING.md) | REST-assured тесты API |

---

## Приватные файлы

| Документ | Описание |
|----------|----------|
| [CREDENTIALS.md](CREDENTIALS.md) | Учётные данные |
| [YOUTRACK_API.md](YOUTRACK_API.md) | YouTrack интеграция |

---

## Структура

```
docs/
├── README.md                    # Этот файл
├── ARCHITECTURE.md              # Архитектура
├── COMPONENTS.md                # Компоненты
├── TASK_TEMPLATE.md             # Шаблон задач
├── DEPLOY_GUIDE.md              # Деплой
├── INFRASTRUCTURE_GUIDE.md      # Инфраструктура
├── TROUBLESHOOTING_GUIDE.md     # Troubleshooting
├── LOAD_TESTING.md              # Load testing
├── CREDENTIALS.md               # Credentials (private)
├── YOUTRACK_API.md              # YouTrack (private)
├── planning/
│   ├── OPTIMIZATION_BACKLOG.md  # Бэклог оптимизаций
│   └── waves/
│       └── Fase4/               # Текущая фаза
└── reports/
    └── lab-optimization-report.md
```

---

## Связанная документация

- **Claude Config:** [/.claude/CLAUDE.md](/.claude/CLAUDE.md) - конфигурация для Claude Code
- **Testing Guide:** [/testing/TESTING.md](/testing/TESTING.md) - E2E тестирование

---

## Окружения

| Env | API | Frontend |
|-----|-----|----------|
| Dev | http://192.168.1.74:31080 | http://192.168.1.74:31081 |
| Prod | http://192.168.1.74:30080 | http://192.168.1.74:30081 |
| Yandex | https://api.wh-lab.ru | https://wh-lab.ru |

---

## Тестовые пользователи

| User | Password | Role |
|------|----------|------|
| admin | admin123 | SUPER_USER |
| wh_north_op | password123 | EMPLOYEE |
| pp_1_op | password123 | EMPLOYEE |

---

*Последнее обновление: 2025-12-12*
