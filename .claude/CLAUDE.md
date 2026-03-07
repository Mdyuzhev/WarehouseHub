# CLAUDE.md — Warehouse Project

## Роль
Технический исполнитель. Задача → Решение. Без вариантов.

---

## 🗺️ Монорепо

```
WarehouseHub/
├── api/                           # Java 17 + Spring Boot 3.2
│   ├── src/main/java/com/warehouse/
│   │   ├── controller/            # 9 controllers (51 endpoints)
│   │   ├── service/               # 17 services
│   │   ├── model/                 # 21 entities
│   │   ├── dto/                   # 27 DTOs
│   │   ├── repository/            # 9 repositories
│   │   └── config/                # Security, Redis, Kafka
│   └── src/main/resources/
│       └── db/migration/          # V2-V13 (12 migrations)
│
├── frontend/                      # Vue.js 3.4 + Vite 5
│   └── src/
│       ├── components/            # 11 (+ documents/)
│       ├── views/                 # 22 (dc/, wh/, pp/)
│       ├── stores/                # facility.js
│       ├── composables/           # useDocument, useFormValidation
│       ├── router/                # 22 routes
│       └── assets/                # facility-themes.css
│
├── testing/                       # Тесты
│   ├── e2e-tests/                 # E2E API тесты (REST-assured)
│   ├── ui-tests/                  # UI тесты (Selenide)
│   ├── TESTING.md
│   └── UI_TESTING_GUIDE.md
│
├── docker-compose.yml             # Homelab — сборка из Dockerfile
├── production/                    # Yandex Cloud — docker pull из registry
├── .github/workflows/             # GitHub Actions (homelab self-hosted runner)
├── Tasks/                         # Задачи для агента
│   ├── *.md                       # Активные задачи
│   └── done/                      # Выполненные задачи
├── .claude/
│   ├── CLAUDE.md                  # Этот файл
│   └── server-access.md           # Подключение к серверу (paramiko)
├── uplink-bot/                    # Python 3.11 + FastAPI (Matrix/Uplink notifications)
│   ├── app.py                     # FastAPI endpoints
│   ├── bot/
│   │   ├── uplink.py              # Uplink webhook client (send_message, send_deploy_event)
│   │   ├── commands.py            # /commands handlers (/status, /pods, /metrics, /robot, /help)
│   │   └── messages.py            # HTML message formatters
│   ├── services/                  # health checks, robot client
│   └── config.py                  # env vars
│
├── docs/
├── telegram-bot/
├── analytics-service/
└── warehouse-robot/
```

---

## 📋 Статус

| Phase | Status | Tests |
|-------|--------|-------|
| 0 Infrastructure | ✅ | - |
| 1 Data Model | ✅ | - |
| 2 Documents | ✅ | - |
| 3 Frontend | ✅ | - |
| 4 E2E Tests | ✅ | 82 passing |

---

## ⚡ Окружения

| Env | API | Frontend | Deploy |
|-----|-----|----------|--------|
| Homelab | 192.168.1.74:8080 | 192.168.1.74:80 | git push main → GitHub Actions (self-hosted runner) |
| Yandex Cloud | api.wh-lab.ru | wh-lab.ru | отключен (закомментирован в workflow) |

| Service | URL | Description |
|---------|-----|-------------|
| Telegram Bot | 192.168.1.74:8000 | bot API + polling |
| Uplink Bot | 192.168.1.74:8001 | Matrix notifications via Uplink botservice |
| Prometheus | 192.168.1.74:9090 | metrics scraping |
| Grafana | 192.168.1.74:3001 | dashboards (admin/admin) |

**Homelab:** `/opt/warehouse`
**Runner:** `~/actions-runner/` (systemd сервис, автозапуск)
**Запуск:** `docker compose up --build -d`

---

## 📋 Работа с задачами

### Как брать задачу

1. Посмотри что есть в `Tasks/`:
   - Один файл → берёшь его
   - Несколько файлов → предложи выбор пользователю
   - Пусто → спроси что делать

2. Прочитай задачу целиком перед началом

### После выполнения задачи

1. Обнови `CLAUDE.md` если изменились: окружения, порты, команды, структура проекта
2. Перенеси файл задачи в `Tasks/done/`

### Как писать задачи

Задача должна содержать:
- **Цель** — что должно работать по итогу
- **Шаги** — конкретные действия (не "сделай лучше", а "замени X на Y")
- **Критерии готовности** — как проверить что задача выполнена
- **Ограничения** — что НЕ трогать

---

## 🔑 Пользователи и роли

| Роль | Описание |
|------|----------|
| `SUPER_USER` | Полный доступ |
| `EMPLOYEE` | Создание документов, ship, deliver, complete |

**В системе только 2 роли. MANAGER/ADMIN в тестах = SUPER_USER.**

### Тестовые пользователи

| User | Password | Role | Facility |
|------|----------|------|----------|
| admin | admin123 | SUPER_USER | - |
| wh_north_op | password123 | EMPLOYEE | WH-C-001 (id=2) |
| wh_south_op | password123 | EMPLOYEE | WH-C-002 (id=3) |
| pp_1_op | password123 | EMPLOYEE | PP-C-001 (id=4) |
| pp_2_op | password123 | EMPLOYEE | PP-C-002 (id=5) |

---

## 🏢 Facilities

| ID | Code | Type | Issue Acts |
|----|------|------|------------|
| 1 | DC-C-001 | DC | ❌ |
| 2 | WH-C-001 | WH | ❌ |
| 3 | WH-C-002 | WH | ❌ |
| 4 | PP-C-001 | PP | ✅ |
| 5 | PP-C-002 | PP | ✅ |
| 6 | PP-C-003 | PP | ✅ |
| 7 | PP-C-004 | PP | ✅ |

**Issue Acts только для PP!**

---

## 📊 API Endpoints (51)

| Controller | Base | Count |
|------------|------|-------|
| Auth | /api/auth | 4 |
| Products | /api/products | 5 |
| Facilities | /api/facilities | 8 |
| Stock | /api/stock | 8 |
| Notifications | /api/notifications | 3 |
| Receipts | /api/receipts | 7 |
| Shipments | /api/shipments | 7 |
| IssueActs | /api/issue-acts | 4 |
| InventoryActs | /api/inventory-acts | 5 |

---

## 🤖 Uplink Bot (Matrix)

**Отправка уведомлений** в Matrix через Uplink botservice webhook.
Бот `@bot_wh_ci:uplink.wh-lab.ru` → комната `#CI` (пространство WAREHOUSE).

| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Health check |
| /send | POST | Отправить произвольное сообщение |
| /deploy/notify | POST | Уведомление о деплое (из CI) |
| /robot/notify | POST | Уведомление от робота |
| /health/notify | POST | Проверка инфры + отправка отчёта |
| /incoming | POST | Входящие команды из Matrix |

**Команды** (через `/incoming` от botservice):
`/status` `/pods` `/metrics` `/robot` `/help`

**Env vars:** `UPLINK_WEBHOOK_URL`, `UPLINK_WEBHOOK_TOKEN`
**Webhook:** `https://uplink.wh-lab.ru/hooks/wh_ci`
**CI notify:** workflow step "Notify Uplink" ждёт readiness перед отправкой.

---

## 🔄 State Machines

```
Receipt:   DRAFT → APPROVED → CONFIRMED → COMPLETED
Shipment:  DRAFT → APPROVED → SHIPPED → DELIVERED
IssueAct:  DRAFT → COMPLETED
Inventory: DRAFT → APPROVED → COMPLETED
```

---

## 🧪 Тесты

### E2E API (REST-assured)

```bash
cd testing/e2e-tests
./mvnw test
./mvnw test -Dtest="ReceiptsApiTest"
```

| Class | Tests |
|-------|-------|
| ReceiptsApiTest | 22 |
| ShipmentsApiTest | 21 |
| IssueActsApiTest | 18 |
| InventoryActsApiTest | 21 |
| **Total** | **82** |

```java
// ПРАВИЛЬНО — REST-assured возвращает Integer, не Long
Long id = extractLong(response.path("id"));
// Issue Acts только для PP
private static final Long TEST_FACILITY_ID = 4L;
```

### UI (Selenide)

```bash
cd testing/ui-tests
./mvnw test
./mvnw test -Dtest="LoginTest"
```

```java
// Всегда fallback селекторы
$("[data-testid='button'], .btn-primary, button[type='submit']")
// Timeout для SPA
element.shouldBe(visible, Duration.ofSeconds(15));
```

### API Integration

```bash
cd api
./mvnw test -Dtest="*IntegrationTest"
```

- НЕ использовать `@Transactional` на тестах
- `@AfterEach` для cleanup: `repository.deleteAll()`

---

## 📁 Ключевые пути

| Type | Path |
|------|------|
| Controllers | api/src/main/java/com/warehouse/controller/ |
| Services | api/src/main/java/com/warehouse/service/ |
| Models | api/src/main/java/com/warehouse/model/ |
| Migrations | api/src/main/resources/db/migration/ |
| E2E Tests | testing/e2e-tests/src/test/java/com/warehouse/e2e/tests/ |
| UI Tests | testing/ui-tests/src/test/java/com/warehouse/ui/ |
| Uplink Bot | uplink-bot/ |
| E2E Guide | testing/TESTING.md |
| UI Guide | testing/UI_TESTING_GUIDE.md |
| Server access | .claude/server-access.md |

---

## 🛠️ Deploy

### Схема

```
git push main
  → GitHub Actions
      └── deploy-homelab (self-hosted runner) → git pull → docker compose up --build -d
      # deploy-yandex — закомментирован в workflow
```

### Подключение к серверу (только paramiko — не голый ssh!)

```python
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.1.74', username='flomaster', password='Misha2021@1@', timeout=10)
stdin, stdout, stderr = client.exec_command('КОМАНДА')
print(stdout.read().decode('utf-8', errors='replace').strip())
client.close()
```

**Полный гайд:** `.claude/server-access.md`

### Ручной деплой на homelab

```python
import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.1.74', username='flomaster', password='Misha2021@1@', timeout=300)
cmds = [
    ('pull',  'cd /opt/warehouse && git pull 2>&1'),
    ('up',    'cd /opt/warehouse && docker compose up --build -d 2>&1 | tail -20'),
    ('check', 'docker ps --format "{{.Names}}\t{{.Status}}" | grep warehouse'),
]
for name, cmd in cmds:
    print(f'--- {name} ---')
    _, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace').strip())
client.close()
```

### Health Check

```
curl http://192.168.1.74:8080/actuator/health
curl http://192.168.1.74:80/
```

---

## 🚨 Критические правила

| ❌ НЕ делать | ✅ Делать |
|-------------|----------|
| `kubectl` / `k3s` команды | `docker compose` команды |
| Голый `ssh` на Windows | `python -c "import paramiko..."` |
| Hardcode IP/порт в коде | `getApiUrl()` из `utils/apiConfig.js` |
| Flyway без проверки версий | `ls api/src/main/resources/db/migration/` |
| Issue Acts для DC/WH | Issue Acts только для PP |
| `response.path("id")` as Long | `extractLong(response.path("id"))` |

---

## 📝 Паттерны кода

```java
// Controller
@RestController @RequestMapping("/api/entities")
@RequiredArgsConstructor
public class EntityController {
    @GetMapping
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE')")
    public ResponseEntity<List<EntityDTO>> getAll() { ... }

    @PostMapping("/{id}/approve")
    @PreAuthorize("hasAnyRole('SUPER_USER')")
    public ResponseEntity<EntityDTO> approve(@PathVariable Long id) { ... }
}
```

---

## 🔄 Git Workflow

| Ветка | Триггер |
|-------|---------|
| main | push → GitHub Actions → homelab + Yandex Cloud |

**Коммит:** `type: описание` (feat, fix, refactor, docs, chore)

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| `docs/ARCHITECTURE.md` | Архитектура системы |
| `testing/TESTING.md` | E2E API тесты |
| `testing/UI_TESTING_GUIDE.md` | UI тесты (Selenide) |
| `telegram-bot/UPLINK_INTEGRATION.md` | Uplink интеграция (гайд) |
| `.claude/server-access.md` | Подключение к серверу |

---

*Updated: 2026-03-07 — Added uplink-bot (Matrix notifications + /commands)*
