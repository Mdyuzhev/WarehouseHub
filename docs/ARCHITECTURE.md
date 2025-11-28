# 🏗️ АРХИТЕКТУРА РЕПОЗИТОРИЕВ WAREHOUSE

## 📋 Обзор

Проект Warehouse разделён на три репозитория с чётким разделением ответственности:

| Репозиторий | Назначение | CI Pipeline |
|-------------|------------|-------------|
| **warehouse-master** | Оркестрация, деплой, тесты, бот | Ручные триггеры деплоя |
| **warehouse-api** | Spring Boot REST API | validate → build → test → package |
| **warehouse-frontend** | Vue.js SPA | lint → build → package |

---

## 🎯 WAREHOUSE-MASTER

**Мастер-репозиторий для оркестрации всей инфраструктуры.**

### Структура:
```
warehouse-master/
├── .gitlab-ci.yml           # Главный пайплайн
├── k8s/                     # ВСЕ K8s манифесты
│   ├── warehouse/           # API + Frontend
│   ├── loadtest/            # Locust
│   ├── notifications/       # Telegram Bot
│   └── monitoring/          # Prometheus
├── telegram-bot/            # Исходники бота
│   ├── app.py
│   ├── claude_proxy.py
│   └── Dockerfile
└── .claude/                 # Контекст для AI агента
    ├── project-context.md
    └── settings.local.json
```

### Доступные действия (ручные триггеры):

| Действие | Описание |
|----------|----------|
| `deploy-api-staging` | Деплой API в K8s |
| `deploy-frontend-staging` | Деплой Frontend в K8s |
| `deploy-all-staging` | Деплой всего в K8s |
| `deploy-api-prod` | Деплой API на Yandex Cloud |
| `deploy-frontend-prod` | Деплой Frontend на Yandex Cloud |
| `deploy-all-prod` | Деплой всего на prod |
| `run-e2e-tests` | Запуск E2E тестов + Allure отчёт |
| `run-load-tests` | Нагрузочное тестирование Locust |
| `deploy-telegram-bot` | Деплой бота в K8s |

---

## 🔧 WAREHOUSE-API

**Только бизнес-логика API. Никакого деплоя!**

### CI Pipeline:
```
validate → build → test → package
```

### Что делает:
1. **validate** - Проверка pom.xml
2. **build** - Компиляция Java
3. **test** - Unit тесты (без E2E!)
4. **package** - Сборка JAR, Docker образ, push в Registry, импорт в K3s

### Результат:
- Docker образ `warehouse-api:latest` в K3s
- Docker образ в Yandex Registry

---

## 🎨 WAREHOUSE-FRONTEND

**Только UI код. Никакого деплоя!**

### CI Pipeline:
```
lint → build → package
```

### Что делает:
1. **lint** - Проверка кода (опционально)
2. **build** - Сборка Docker образа (multi-stage)
3. **package** - Push в Registry, импорт в K3s

### Результат:
- Docker образ `warehouse-frontend:latest` в K3s
- Docker образ в Yandex Registry

---

## 🔄 РАБОЧИЙ ПРОЦЕСС

### Разработка:
1. Разработчик пушит код в `warehouse-api` или `warehouse-frontend`
2. CI автоматически собирает и публикует образ
3. Образ готов к деплою

### Деплой:
1. Переходим в `warehouse-master` → CI/CD → Pipelines
2. Запускаем нужный деплой (staging или prod)
3. Профит!

### Тестирование:
1. В `warehouse-master` запускаем `run-e2e-tests`
2. Смотрим Allure отчёт
3. Или запускаем через Telegram бота!

---

## 🤖 CLAUDE AI ИНТЕГРАЦИЯ

Контекст для Claude AI агента хранится в `warehouse-master/.claude/`:

- **project-context.md** - Вся информация о проекте, URL, креды
- **settings.local.json** - Настройки Claude Code

При запуске задач через Telegram бота, Claude читает этот контекст и знает:
- Структуру проекта
- URL всех сервисов
- Креды для YouTrack
- Workflow правила

---

## 📊 ПРЕИМУЩЕСТВА

| Было | Стало |
|------|-------|
| Всё в одном репо | Чёткое разделение |
| 10+ stages в pipeline | 4 stages для сборки |
| Деплой зашит в API | Деплой централизован |
| Сложно деплоить отдельно | Независимый деплой |

---

## 🔗 ССЫЛКИ

- **GitLab:** http://192.168.1.74:8080
- **Staging API:** http://192.168.1.74:30080
- **Staging Frontend:** http://192.168.1.74:30081
- **Production:** https://wh-lab.ru
- **Allure:** http://192.168.1.74:5252
