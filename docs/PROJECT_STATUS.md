# Project Status - Warehouse

> Актуальный статус проекта на 2025-12-02. Используй этот файл для понимания текущего контекста перед планированием задач.

---

## Текущая ситуация в репозиториях

### warehouse-master
| Параметр | Значение |
|----------|----------|
| **Активная ветка** | `feature/WH-217-load-testing-workflow` |
| **Статус** | Clean (готов к merge в main) |
| **Последний коммит** | `b95d4ff` - k6 Kafka для Production |
| **Ветки** | main, feature/WH-217-load-testing-workflow |

**Что в ветке WH-217:**
- Telegram Bot v5.6 с Unified QA Menu
- Load Testing Wizard (7 шагов)
- Cleanup Service (Redis/Kafka/PostgreSQL)
- k6 Kafka для Production (KAFKA_PROD_BROKERS)
- Cooldown 30 минут между нагрузочными тестами
- kubectl в контейнере бота (WH-267, WH-268)

**Готово к:**
- Merge в main
- Production деплой v5.6

---

### warehouse-api
| Параметр | Значение |
|----------|----------|
| **Активная ветка** | `main` |
| **Последний коммит** | `WH-269` - Facilities Management + bugfixes |
| **Ветки** | main, develop |

**Что в main:**
- ✅ WH-269: Facilities Management (DC → WH → PP иерархия)
- ✅ WH-378: Bugfixes (Flyway для тестов, FacilityRepository optional, JWT backward compatibility)
- ✅ CI/CD pipeline для dev/prod окружений
- ✅ Redis JWT token caching (WH-103)
- ✅ Git workflow + MR шаблоны (WH-190, WH-191)

**Статус:**
- ✅ Production deployment успешен
- ✅ Все тесты проходят (24/24)

---

### warehouse-frontend
| Параметр | Значение |
|----------|----------|
| **Активная ветка** | `develop` |
| **Последний коммит** | `c033eb7` - Dual Environment CI/CD |
| **Ветки** | main, develop |

**Что в develop:**
- CI/CD pipeline для dev/prod окружений
- Analytics URL fixes для production
- Git workflow + MR шаблоны

**Статус:**
- develop готов к merge в main
- CI/CD работает (auto deploy в warehouse-dev)

---

## Активные задачи в YouTrack (State != Fixed)

### Критичные (для релиза v5.6)

| ID | Задача | Приоритет |
|----|--------|-----------|
| WH-265 | [Деплой] Commit + Push + обновить WH-217 | HIGH |
| WH-264 | [Деплой] Smoke test в Telegram | HIGH |
| WH-263 | [Деплой] Import в K3s и deploy | HIGH |
| WH-262 | [Деплой] Build Docker image v5.6.0 | HIGH |
| WH-261 | [Деплой] Локальное тестирование бота | HIGH |

### Документация

| ID | Задача |
|----|--------|
| WH-260 | Создать RELEASE_NOTES для v5.6.0 |
| WH-259 | Обновить /help команду — добавить новые команды |
| WH-258 | Обновить версию в app.py на 5.6.0 |
| WH-257 | Обновить docs/LOAD_TESTING.md — Telegram-бот |
| WH-256 | Обновить docs/TESTING.md — новый workflow НТ |

### Код (Telegram Bot v5.6)

| ID | Задача |
|----|--------|
| WH-266 | Убрать дублирование нагрузочного тестирования из QA меню |
| WH-255 | [Роутинг] Обновить импорты из handlers |
| WH-254 | [Роутинг] Callback роутинг для cleanup wizard |
| WH-253 | [Роутинг] Callback роутинг для нового wizard |
| WH-252 | [Роутинг] Обработка кнопок НТ в process_command() |

### Нагрузочное тестирование (k6 Kafka)

| ID | Задача |
|----|--------|
| WH-216 | Документация процедуры и результатов |
| WH-215 | Запуск Kafka НТ в Telegram-бот (QA меню) |
| WH-214 | Grafana дашборд Kafka Load Testing |
| WH-213 | Baseline-тестирование и фиксация результатов |
| WH-212 | Отправка метрик k6 в Prometheus |

---

## Инфраструктура

### Staging (192.168.1.74)

**K8s Namespaces:**

| Namespace | Сервисы | Статус |
|-----------|---------|--------|
| **warehouse** | API (2 replicas), Frontend, Robot, Analytics, PostgreSQL, Redis, Kafka | ✅ Running |
| **warehouse-dev** | API (1 replica), Frontend, PostgreSQL, Redis | ✅ Running |
| **loadtest** | Locust (master + 5 workers), k6-operator | ✅ Running |
| **notifications** | Telegram Bot v5.5 (нужен upgrade до v5.6) | ✅ Running |
| **monitoring** | Prometheus, Grafana, Alertmanager | ✅ Running |

**Порты (Production):**
- API: 30080
- Frontend: 30081
- Robot: 30070
- Analytics: 30091
- Telegram Bot: 30088
- Locust UI: 30089
- Grafana: 30300

**Порты (Dev):**
- API: 31080
- Frontend: 31081
- PostgreSQL: 31432
- Redis: 31379

---

### Production (130.193.44.34)

| Сервис | URL | Статус |
|--------|-----|--------|
| API | https://api.wh-lab.ru | ✅ UP |
| Frontend | https://wh-lab.ru | ✅ UP |
| Analytics | (internal) | ✅ UP |
| Kafka | :29092 | ✅ UP |

**Docker Compose:**
- warehouse-api, warehouse-frontend, warehouse-analytics
- kafka, redis, postgres
- nginx, certbot

---

## CI/CD Pipeline (WH-200)

### Dual Environment Workflow

| Ветка | Окружение | Namespace | Порты | Деплой |
|-------|-----------|-----------|-------|--------|
| `develop` | Development | warehouse-dev | 31xxx | **Auto** |
| `main` | Production | warehouse | 30xxx | **Manual** |

**Статус:**
- ✅ warehouse-api: CI/CD настроен
- ✅ warehouse-frontend: CI/CD настроен
- ⏳ warehouse-master: только manual jobs

**Процесс:**
```
develop → push → auto deploy → warehouse-dev (31xxx)
        ↓
    MR в main
        ↓
main → push → manual deploy → warehouse (30xxx)
```

---

## Последние крупные изменения

### WH-269 + WH-378: Facilities Management (warehouse-api)
**Дата:** 2025-12-02
**Ветка:** main
**Статус:** ✅ В production

**Изменения:**
- Facilities Management — трёхуровневая иерархия объектов (DC → WH → PP)
- Flyway migration V2__add_facilities.sql
- FacilityController, FacilityService, FacilityRepository
- JWT claims расширены (facilityType, facilityId, facilityCode)
- Backward compatibility для JWT без facility claims
- 24 тестa проходит (19 существующих + 5 новых JwtServiceTest)
- FacilityRepository сделан optional (@Autowired(required=false))
- Flyway отключен для тестов (spring.flyway.enabled=false)

### WH-217: Unified QA Menu + Load Testing Workflow (v5.6)
**Дата:** 2025-12-02
**Ветка:** feature/WH-217-load-testing-workflow
**Статус:** Готово к merge

**Изменения:**
- Load Testing Wizard — 7 шагов (среда → пароль → сценарий → VU → время → паттерн → confirm)
- Cleanup Service — Redis FLUSHDB, Kafka consumer groups, PostgreSQL
- k6 Kafka для Production (KAFKA_PROD_BROKERS: 130.193.44.34:29092)
- Cooldown 30 минут между нагрузочными тестами
- kubectl в контейнере бота (WH-267, WH-268)

---

### WH-200: Dual Environment CI/CD
**Дата:** 2025-11-30
**Ветки:** develop (в обоих репозиториях API/Frontend)
**Статус:** В production

**Изменения:**
- Автоматический деплой в warehouse-dev при push в develop
- Ручной деплой в warehouse при push в main
- ResourceQuota для dev (4 CPU, 8Gi Memory)
- GitLab Environments (development, production)

---

### WH-103: Нагрузочное тестирование + оптимизация
**Дата:** 2025-11-28
**Статус:** В production

**Результаты:**
- Safe режим: 150 VU, 63 RPS, 0% ошибок
- Max режим: 350-400 VU, 40-50 RPS, <2% ошибок
- Redis JWT token caching
- 2 реплики API с 1500m CPU

---

## Что дальше (Next Steps)

### Приоритет 1: Релиз v5.6 (Telegram Bot)
1. ✅ Merge WH-217 в main
2. ⏳ Обновить версию в app.py (WH-258)
3. ⏳ Обновить /help команду (WH-259)
4. ⏳ Создать RELEASE_NOTES (WH-260)
5. ⏳ Build Docker image v5.6.0 (WH-262)
6. ⏳ Deploy в K3s (WH-263)
7. ⏳ Smoke test (WH-264)

### Приоритет 2: Документация
1. ⏳ Обновить docs/LOAD_TESTING.md (WH-257)
2. ⏳ Обновить docs/TESTING.md (WH-256)
3. ⏳ Документировать k6 Kafka результаты (WH-216)

### Приоритет 3: Merge develop → main
1. ⏳ warehouse-api: develop → main (CI/CD)
2. ⏳ warehouse-frontend: develop → main (CI/CD)

### Приоритет 4: k6 Kafka Testing
1. ⏳ Baseline тесты (WH-213)
2. ✅ Grafana дашборд (WH-214) — частично
3. ⏳ Интеграция в Telegram (WH-215) — уже есть

---

## Технические долги

### Высокий приоритет
- Дублирование нагрузочного тестирования в QA меню (WH-266)
- Cleanup wizard routing (WH-254)
- Load test wizard routing (WH-253)

### Средний приоритет
- PostgreSQL репликация (read replica настроена, но не используется)
- Alerting в Telegram (Alertmanager настроен, но не интегрирован)
- API rate limiting (настроен, но не протестирован под нагрузкой)

### Низкий приоритет
- Cloudflared tunnels нестабильны (URL меняются при рестарте)
- Selenoid в Docker дублируется с K8s версией
- Orchestrator UI не используется

---

## Критичные напоминания

### K3s / containerd
```bash
# ОБЯЗАТЕЛЬНЫЙ процесс деплоя:
docker rmi IMAGE:TAG
docker build --no-cache -t IMAGE:TAG .
sudo k3s ctr images rm docker.io/library/IMAGE:TAG
docker save IMAGE:TAG | sudo k3s ctr images import -
kubectl delete pod -n NAMESPACE -l app=APP_LABEL
```

### YouTrack API
```bash
# ТОЛЬКО Basic Auth!
curl -s -u 'admin:Misha2021@1@' 'http://192.168.1.74:8088/api/issues/WH-XXX'
```

### Protected Branches
- НЕ пушить напрямую в main!
- Создавать feature branches
- Использовать Merge Requests

---

## Метрики проекта

### Кодовая база
| Репозиторий | Технологии | Размер |
|-------------|------------|--------|
| warehouse-api | Java 17, Spring Boot 3.2 | ~15K LOC |
| warehouse-frontend | Vue.js 3.4, Vite 5 | ~8K LOC |
| warehouse-master | Python, Bash, K8s YAML | ~20K LOC |

### Инфраструктура
- **K8s Pods:** ~25 (все namespaces)
- **Docker Images:** 8 основных + браузеры Selenoid
- **K8s Namespaces:** 5
- **Порты:** 15+ NodePort сервисов

### Тестирование
- **E2E тесты:** RestAssured (Java)
- **UI тесты:** Selenide + Allure
- **Load testing:** Locust (HTTP), k6 (Kafka)
- **Браузеры:** Chrome 127/128, Firefox 125

---

## Контакты и доступы

### Серверы
- Staging: 192.168.1.74 (flomaster)
- Production: 130.193.44.34 (ubuntu)

### Сервисы
- GitLab: http://192.168.1.74:8080 (root:Misha2021@1@)
- YouTrack: http://192.168.1.74:8088 (admin:Misha2021@1@)
- Grafana: http://192.168.1.74:30300 (admin:admin123)

### Telegram Bot
- Token: `8532494921:AAEoxQ87qQVcutgCSa8d8DntT_47xhvrCAI`
- Chat ID: `290274837`

---

## Для Claude CLI: Quick Start

### Когда начинаешь работу:
```bash
# 1. Прочитать этот файл (PROJECT_STATUS.md)
# 2. Проверить health
curl http://192.168.1.74:30080/actuator/health
# 3. Проверить git status
cd /home/flomaster/warehouse-master && git status
# 4. Прочитать связанные docs:
#    - ARCHITECTURE.md (архитектура)
#    - COMPONENTS.md (компоненты)
#    - TROUBLESHOOTING_GUIDE.md (проблемы)
```

### Типичные сценарии:

**Деплой сервиса:**
```bash
cd ~/warehouse-master/SERVICE_DIR
# См. docs/DEPLOY_GUIDE.md (7 шагов)
```

**Создание задачи в YouTrack:**
```bash
# См. docs/YOUTRACK_API.md (примеры)
curl -s -u 'admin:Misha2021@1@' -X POST \
  'http://192.168.1.74:8088/api/issues?fields=id,idReadable' \
  -H 'Content-Type: application/json' \
  -d '{"project":{"id":"0-1"},"summary":"Название"}'
```

**Проверка логов:**
```bash
kubectl logs -n warehouse -l app=warehouse-api --tail=100
```

---

*Последнее обновление: 2025-12-02*
