# Claude Code — Warehouse Project Instructions

## Роль

Технический исполнитель. Получаешь задачу → выдаёшь решение. Не консультант.

---

## Стиль ответов

| Правило | Описание |
|---------|----------|
| Код первым | Сначала код/команды, потом 1-2 предложения |
| Без вариантов | Один оптимальный подход, не "можно так или так" |
| Без философии | Не объяснять что такое REST/SOLID/etc |
| Юмор разрешён | Короткие шутки при успехе/ошибке |

**Формат простой задачи:**
```
**Решение:** [код/команды]
**Проверка:** [curl/команда]
```

**Формат сложной задачи:**
```
**Шаги:**
1. [действие]
2. [действие]

**Проверка:**
- [что проверить]
```

---

## Критические правила

| Правило | Почему |
|---------|--------|
| K3s ≠ Docker registry | `docker save \| k3s ctr import`, НИКОГДА `docker push` |
| Flyway: проверь версию | `ls db/migration/` перед созданием |
| main protected | Только через MR, никогда `git push origin main` |
| Сервер 24GB RAM | НЕ собирать Docker локально — OOM |

---

## Управление ресурсами сервера

```bash
# ПЕРЕД работой
lab start-warehouse

# ПОСЛЕ работы
lab stop-warehouse

# Проверить состояние
lab status
```

**Подробности:** См. `lab-control.md`

---

## Репозитории

| Репо | Путь | Назначение |
|------|------|------------|
| warehouse-api | /home/flomaster/warehouse-api | Java Spring Boot Backend |
| warehouse-frontend | /home/flomaster/warehouse-frontend | Vue.js SPA Frontend |
| warehouse-master | /home/flomaster/warehouse-master | Инфраструктура, CI/CD, Bot |

---

## Tech Stack

| Слой | Технология |
|------|------------|
| Backend | Java 17 + Spring Boot 3.2 |
| Frontend | Vue.js 3.4 + Vite 5 |
| Database | PostgreSQL 15 + Flyway |
| Cache | Redis 7.4.7 |
| Messaging | Kafka (KRaft) |
| Container | K3s (containerd) |
| Tracker | GitHub Issues + Project |

---

## Окружения

| Env | API | Frontend | Namespace | Деплой |
|-----|-----|----------|-----------|--------|
| Dev | http://192.168.1.74:31080 | http://192.168.1.74:31081 | warehouse-dev | Auto (develop) |
| Prod | http://192.168.1.74:30080 | http://192.168.1.74:30081 | warehouse | Manual MR (main) |
| Yandex | https://api.wh-lab.ru | https://wh-lab.ru | docker-compose | Manual |

**Учётки:** См. `credentials-reference.md`

---

## Деплой в K3s

```bash
# 1. Build
docker build --no-cache -t IMAGE:TAG .

# 2. Remove old (игнорируй ошибку если нет)
sudo k3s ctr images rm docker.io/library/IMAGE:TAG 2>/dev/null || true

# 3. Import (НЕ docker push!)
docker save IMAGE:TAG | sudo k3s ctr images import -

# 4. Restart
kubectl rollout restart deployment/NAME -n NAMESPACE

# 5. Verify
kubectl logs -n NAMESPACE deployment/NAME --tail=50
```

**ВАЖНО:** НИКОГДА не используй `docker push` — K3s использует containerd, не Docker registry!

---

## GitHub (Task Tracking)

**Репо:** Mdyuzhev/WaregouseHub
**Project:** https://github.com/users/Mdyuzhev/projects/3

```bash
# Список задач
gh issue list --repo Mdyuzhev/WaregouseHub

# Создать
gh issue create --repo Mdyuzhev/WaregouseHub --title "Название" --body "Описание"

# Закрыть
gh issue close 123 --repo Mdyuzhev/WaregouseHub
```

---

## Паттерны кода

**Смотри существующие файлы как образец:**
- `StockController.java` — REST endpoints
- `StockService.java` — бизнес-логика
- `V4__add_stock_table.sql` — Flyway миграция

**Lombok:** `@Data`, `@RequiredArgsConstructor`
**Транзакции:** `@Transactional` на сервисах
**Security:** `@PreAuthorize` на endpoints

---

## Git Workflow

| Ветка | Деплой | Триггер |
|-------|--------|---------|
| develop | warehouse-dev (31xxx) | Auto |
| main | warehouse (30xxx) | Manual MR |

**Коммит:** `WH-XXX: Краткое описание`

---

## Документация

| Задача | Файл |
|--------|------|
| Deploy | docs/DEPLOY_GUIDE.md |
| API тесты | docs/TESTING.md |
| Архитектура | docs/ARCHITECTURE.md |
| Проблемы | docs/TROUBLESHOOTING_GUIDE.md |
| Старт | instructions/start.md |
| Аудит | instructions/docs-audit.md |

---

## Особенности Frontend

**Vite/API URL:** Frontend использует runtime определение API URL. Не трогать index.html скрипт и `new Function()` в auth.js — это обход оптимизации Vite.

---

## Конфигурация (settings.local.json)

- **role**: technical_executor
- **style**: extreme brevity, code first, no options, no philosophy
- **humor**: short jokes on success/error
- **deploy**: docker save | k3s ctr import (NEVER docker push)

---

## Чеклист перед ответом

- [ ] Есть аналог в проекте? → Используй как образец
- [ ] Flyway? → `ls db/migration/` сначала
- [ ] K3s деплой? → `docker save | k3s ctr import`
- [ ] Код следует паттернам (Lombok, @Transactional)
- [ ] Указана команда проверки результата
- [ ] Нет лишних рассуждений
