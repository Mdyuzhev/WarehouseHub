# Warehouse Project — Claude Config

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
├── testing/                       # E2E тесты (82 passing)
│   ├── e2e-tests/                 # REST-assured + JUnit 5
│   └── TESTING.md                 # Гайд по написанию тестов
│
├── docs/                          # Документация (оптимизировано)
│   ├── README.md                  # Навигация
│   ├── TASK_TEMPLATE.md           # Как ставить задачи
│   ├── ARCHITECTURE.md            # Архитектура
│   └── ...                        # Guides
│
├── k8s/                           # Kubernetes manifests
├── telegram-bot/                  # Notification bot
├── analytics-service/             # Kafka consumer
└── warehouse-robot/               # Simulation
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

| Env | API | Frontend |
|-----|-----|----------|
| Dev | :31080 | :31081 |
| Prod | :30080 | :30081 |
| Yandex | api.wh-lab.ru | wh-lab.ru |

**Host:** 192.168.1.74

---

## 🔑 Пользователи и роли

### Роли в системе

| Роль | Описание |
|------|----------|
| `SUPER_USER` | Полный доступ (admin) |
| `EMPLOYEE` | Создание документов, ship, deliver, complete |

**Важно:** В системе только 2 роли. MANAGER/ADMIN в тестах = admin (SUPER_USER).

### Тестовые пользователи

| User | Password | Role | Facility |
|------|----------|------|----------|
| admin | admin123 | SUPER_USER | - |
| wh_north_op | password123 | EMPLOYEE | WH-C-001 (id=2) |
| wh_south_op | password123 | WH-C-002 (id=3) |
| pp_1_op | password123 | EMPLOYEE | PP-C-001 (id=4) |
| pp_2_op | password123 | EMPLOYEE | PP-C-002 (id=5) |

### Права по операциям

| Операция | EMPLOYEE | SUPER_USER |
|----------|----------|------------|
| Create | ✅ | ✅ |
| View | ✅ | ✅ |
| Approve | ❌ | ✅ |
| Ship/Deliver/Complete | ✅ | ✅ |
| Cancel/Delete | ❌ | ✅ |

---

## 🏢 Facilities

| ID | Code | Type | Для Issue Acts |
|----|------|------|----------------|
| 1 | DC-C-001 | DC | ❌ |
| 2 | WH-C-001 | WH | ❌ |
| 3 | WH-C-002 | WH | ❌ |
| 4 | PP-C-001 | PP | ✅ |
| 5 | PP-C-002 | PP | ✅ |
| 6 | PP-C-003 | PP | ✅ |
| 7 | PP-C-004 | PP | ✅ |

**Issue Acts только для PP (Pickup Points)!**

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

## 🔄 State Machines

```
Receipt:   DRAFT → APPROVED → CONFIRMED → COMPLETED
Shipment:  DRAFT → APPROVED → SHIPPED → DELIVERED
IssueAct:  DRAFT → COMPLETED
Inventory: DRAFT → APPROVED → COMPLETED
```

---

## 🧪 E2E Тесты

### Запуск

```bash
cd testing/e2e-tests
./mvnw test                                    # Все тесты
./mvnw test -Dtest="ReceiptsApiTest"           # Один класс
./mvnw test -Dtest="*ApiTest"                  # По паттерну
```

### Статистика

| Test Class | Tests |
|------------|-------|
| ReceiptsApiTest | 22 |
| ShipmentsApiTest | 21 |
| IssueActsApiTest | 18 |
| InventoryActsApiTest | 21 |
| **Total** | **82** |

### Важные правила тестов

```java
// REST-assured возвращает Integer, не Long!
// НЕПРАВИЛЬНО:
Long id = response.path("id");  // ClassCastException

// ПРАВИЛЬНО:
Long id = extractLong(response.path("id"));

// Issue Acts только для PP (id >= 4)
private static final Long TEST_FACILITY_ID = 4L;  // PP-C-001
```

**Полный гайд:** `testing/TESTING.md`

---

## 📁 Ключевые пути

### API
| Type | Path |
|------|------|
| Controllers | api/src/main/java/com/warehouse/controller/ |
| Services | api/src/main/java/com/warehouse/service/ |
| Models | api/src/main/java/com/warehouse/model/ |
| Migrations | api/src/main/resources/db/migration/ |

### Testing
| Type | Path |
|------|------|
| E2E Tests | testing/e2e-tests/src/test/java/com/warehouse/e2e/tests/ |
| Base Class | testing/e2e-tests/.../base/BaseE2ETest.java |
| Config | testing/e2e-tests/.../config/TestConfig.java |
| Guide | testing/TESTING.md |

### Docs
| Type | Path |
|------|------|
| Navigation | docs/README.md |
| Task Template | docs/TASK_TEMPLATE.md |
| Architecture | docs/ARCHITECTURE.md |

---

## 🛠️ Deploy

### API

```bash
cd api
docker build --no-cache -t warehouse-api:latest .
sudo k3s ctr images rm docker.io/library/warehouse-api:latest 2>/dev/null || true
docker save warehouse-api:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/warehouse-api -n warehouse-dev
```

### Frontend

```bash
cd frontend
docker build --no-cache -t warehouse-frontend:latest .
sudo k3s ctr images rm docker.io/library/warehouse-frontend:latest 2>/dev/null || true
docker save warehouse-frontend:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/warehouse-frontend -n warehouse-dev
```

### Health Check

```bash
curl http://192.168.1.74:31080/actuator/health
curl http://192.168.1.74:31081/
```

---

## 🚨 Критические правила

| ❌ НЕ делать | ✅ Делать |
|-------------|----------|
| `docker push` | `docker save \| k3s ctr import` |
| `git push main` | MR через GitLab |
| Flyway без проверки | `ls api/.../db/migration/` |
| Issue Acts для DC/WH | Issue Acts только для PP |
| `response.path("id")` as Long | `extractLong(response.path("id"))` |

---

## 📝 Паттерны кода

### Controller с SUPER_USER

```java
@RestController @RequestMapping("/api/entities")
@RequiredArgsConstructor
public class EntityController {

    @GetMapping
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    public ResponseEntity<List<EntityDTO>> getAll() { ... }

    @PostMapping("/{id}/approve")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'MANAGER', 'ADMIN')")  // Только менеджеры
    public ResponseEntity<EntityDTO> approve(@PathVariable Long id) { ... }
}
```

### E2E Test

```java
@Test
void employeeCreatesDocument() {
    Long id = extractLong(authRequest(getEmployeeToken())
        .body(Map.of(
            "facilityId", TEST_FACILITY_ID,
            "items", List.of(Map.of("productId", 1L, "quantity", 10))
        ))
    .when()
        .post("/api/documents")
    .then()
        .statusCode(201)
        .body("status", equalTo("DRAFT"))
        .extract()
        .path("id"));
}
```

---

## 🔄 Git Workflow

| Ветка | Порты | Триггер |
|-------|-------|---------|
| develop | 31xxx | Auto deploy |
| main | 30xxx | MR only |

**Коммит:** `type: описание` (feat, fix, refactor, docs, chore)

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| `docs/README.md` | Навигация по документации |
| `docs/TASK_TEMPLATE.md` | Как правильно ставить задачи |
| `docs/ARCHITECTURE.md` | Архитектура системы |
| `testing/TESTING.md` | Гайд по E2E тестам |

---

*Updated: 2025-12-12 — E2E tests passing (82), docs optimized*
