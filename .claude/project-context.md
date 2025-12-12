# Контекст проекта Warehouse

## Роль Claude

Технический исполнитель. Задача → Решение. Без вариантов, без философии.

---

## Стиль ответов

```
ХОРОШО:
**Решение:** `kubectl rollout restart deployment/api -n warehouse`
**Проверка:** `curl http://192.168.1.74:30080/actuator/health`

ПЛОХО:
"Есть несколько способов решить эту задачу. Можно использовать..."
"REST API - это архитектурный стиль, который..."
```

**Юмор:** Короткие шутки разрешены при успехе/ошибке.

---

## Критические правила

| Нарушение | Последствие |
|-----------|-------------|
| `docker push` вместо `k3s ctr import` | Образ не появится в K3s |
| Flyway без проверки версии | Конфликт миграций |
| Push в main напрямую | Rejected (protected) |
| Docker build локально | OOM на сервере 24GB |

---

## Ресурсы сервера

```bash
lab start-warehouse  # ПЕРЕД работой
lab stop-warehouse   # ПОСЛЕ работы
lab status          # Проверить
```

---

## Репозитории

| Репо | Путь | Назначение |
|------|------|------------|
| warehouse-api | /home/flomaster/warehouse-api | Java Spring Boot |
| warehouse-frontend | /home/flomaster/warehouse-frontend | Vue.js SPA |
| warehouse-master | /home/flomaster/warehouse-master | Инфра, CI/CD, Bot |

---

## Окружения

| Env | API | Namespace | Deploy |
|-----|-----|-----------|--------|
| Dev | :31080 | warehouse-dev | auto (develop) |
| Prod | :30080 | warehouse | manual MR (main) |
| Yandex | api.wh-lab.ru | docker-compose | manual |

---

## Деплой K3s (шаблон)

```bash
docker build --no-cache -t IMAGE:TAG .
sudo k3s ctr images rm docker.io/library/IMAGE:TAG 2>/dev/null || true
docker save IMAGE:TAG | sudo k3s ctr images import -
kubectl rollout restart deployment/NAME -n NAMESPACE
kubectl logs -n NAMESPACE deployment/NAME --tail=50
```

---

## GitHub Tasks

```bash
gh issue list --repo Mdyuzhev/WaregouseHub
gh issue create --repo Mdyuzhev/WaregouseHub --title "X" --body "Y"
gh issue close 123 --repo Mdyuzhev/WaregouseHub
```

---

## Учётки

| Env | User | Pass |
|-----|------|------|
| Dev | admin | admin123 |
| Prod | admin | admin123 |
| Prod | employee | password123 |

---

## Паттерны кода

**Образцы:**
- StockController.java — REST
- StockService.java — бизнес-логика  
- V4__add_stock_table.sql — Flyway

**Lombok:** @Data, @RequiredArgsConstructor
**Транзакции:** @Transactional на сервисах
**Security:** @PreAuthorize на endpoints

---

## Git

| Ветка | Deploy | Порты |
|-------|--------|-------|
| develop | auto → warehouse-dev | 31xxx |
| main | MR → warehouse | 30xxx |

**Коммит:** `WH-XXX: Описание`

---

## Документация

| Задача | Файл |
|--------|------|
| Деплой | docs/DEPLOY_GUIDE.md |
| Тесты | docs/TESTING.md |
| Архитектура | docs/ARCHITECTURE.md |
| Проблемы | docs/TROUBLESHOOTING_GUIDE.md |

---

## Vite/API URL (важно!)

Frontend использует runtime определение API URL. Не трогать index.html скрипт и `new Function()` в auth.js — это обход оптимизации Vite.

---

## Чеклист

- [ ] Есть аналог? → Копируй паттерн
- [ ] Flyway? → `ls db/migration/` сначала
- [ ] K3s? → `docker save | k3s ctr import`
- [ ] Команда проверки указана?