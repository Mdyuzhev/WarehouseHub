# WH-271: Test Hierarchy Setup — GitHub Issues

## Story (Parent)

**Title:** [Phase 1] WH-271: Test Hierarchy Setup (DC → WH → PP)

**Body:**
```markdown
## Цель
Создать seed-данные для тестовой иерархии DC → WH → PP с пользователями и остатками.

## Структура
```
DC-C-001 (Центральный РЦ)
├── WH-C-001 (Склад Север)
│   ├── PP-C-001 (ПВЗ 1)
│   └── PP-C-002 (ПВЗ 2)
└── WH-C-002 (Склад Юг)
    ├── PP-C-003 (ПВЗ 3)
    └── PP-C-004 (ПВЗ 4)
```

## Задачи
- [ ] #XXX V5: Seed facilities (7 records)
- [ ] #XXX V6: Seed users (7 operators)
- [ ] #XXX V7: Seed stock records
- [ ] #XXX Integration tests (4 tests)

## Критерии готовности
- [ ] 7 facilities в иерархии DC → WH → PP
- [ ] 7 новых пользователей привязаны к facilities
- [ ] Stock записи для WH и PP объектов
- [ ] Integration test 4/4 passed
- [ ] Dev environment (31080) работает

## Env
- Dev: http://192.168.1.74:31080
- Namespace: warehouse-dev
```

**Labels:** `phase-1`, `data-model`, `story`

---

## Task 1: V5 Seed Facilities

**Title:** WH-271.1: Flyway V5 — seed facilities (7 records)

**Body:**
```markdown
## Задача
Создать миграцию `V5__seed_facilities.sql` с 7 тестовыми facilities.

## Данные
| id | type | code | name | parent_id |
|----|------|------|------|-----------|
| 1 | DC | DC-C-001 | Центральный РЦ | NULL |
| 2 | WH | WH-C-001 | Склад Север | 1 |
| 3 | WH | WH-C-002 | Склад Юг | 1 |
| 4 | PP | PP-C-001 | ПВЗ 1 | 2 |
| 5 | PP | PP-C-002 | ПВЗ 2 | 2 |
| 6 | PP | PP-C-003 | ПВЗ 3 | 3 |
| 7 | PP | PP-C-004 | ПВЗ 4 | 3 |

## Файл
`src/main/resources/db/migration/V5__seed_facilities.sql`

## Образец
`V4__add_stock_table.sql`

## Шаги
1. Проверить версию: `ls src/main/resources/db/migration/`
2. Создать V5__seed_facilities.sql
3. Deploy dev: pipeline или manual
4. Проверить результат

## Checkpoint
```bash
TOKEN=$(curl -s -X POST http://192.168.1.74:31080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

curl -s http://192.168.1.74:31080/api/facilities/tree \
  -H "Authorization: Bearer $TOKEN" | jq '. | length'
# Expected: 7 (или 1 root с children)
```

## Definition of Done
- [ ] V5 миграция создана
- [ ] Deploy на dev успешен
- [ ] `/api/facilities/tree` возвращает 7 facilities
- [ ] Иерархия: 1 DC → 2 WH → 4 PP
```

**Labels:** `flyway`, `backend`, `task`

---

## Task 2: V6 Seed Users

**Title:** WH-271.2: Flyway V6 — seed facility users (7 operators)

**Body:**
```markdown
## Задача
Создать миграцию `V6__seed_facility_users.sql` с операторами для каждого facility.

## Данные
| username | role | facility_type | facility_id | name |
|----------|------|---------------|-------------|------|
| dc_manager | MANAGER | DC | 1 | Менеджер РЦ |
| wh_north_op | EMPLOYEE | WH | 2 | Оператор Север |
| wh_south_op | EMPLOYEE | WH | 3 | Оператор Юг |
| pp_1_op | EMPLOYEE | PP | 4 | Оператор ПВЗ 1 |
| pp_2_op | EMPLOYEE | PP | 5 | Оператор ПВЗ 2 |
| pp_3_op | EMPLOYEE | PP | 6 | Оператор ПВЗ 3 |
| pp_4_op | EMPLOYEE | PP | 7 | Оператор ПВЗ 4 |

## Password
`password123` → BCrypt: `$2a$10$N9qo8uLOickgx2ZMRZoMye.Yjhx/G8SWRuT8KW6UTZiwKfFwF6Q.i`

## Файл
`src/main/resources/db/migration/V6__seed_facility_users.sql`

## Образец
Существующие users в `V1__init.sql`

## Checkpoint
```bash
# Login как wh_north_op
curl -s -X POST http://192.168.1.74:31080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"wh_north_op","password":"password123"}' | jq '.token' | cut -d. -f2 | base64 -d | jq

# Expected в payload:
# "facilityType": "WH"
# "facilityId": 2
# "facilityCode": "WH-C-001"
```

## Definition of Done
- [ ] V6 миграция создана
- [ ] 7 пользователей созданы
- [ ] Login возвращает JWT с facility claims
- [ ] dc_manager имеет role MANAGER
- [ ] Остальные имеют role EMPLOYEE
```

**Labels:** `flyway`, `backend`, `task`

---

## Task 3: V7 Seed Stock

**Title:** WH-271.3: Flyway V7 — seed stock records

**Body:**
```markdown
## Задача
Создать миграцию `V7__seed_stock.sql` с начальными остатками для WH и PP.

## Логика
| facility_id | facility | products | quantity |
|-------------|----------|----------|----------|
| 2 | WH-C-001 | 1,2,3,4,5 | 50-200 |
| 3 | WH-C-002 | 1,2,3,4,5 | 50-200 |
| 4 | PP-C-001 | 1,2,3 | 10-50 |
| 5 | PP-C-002 | 1,2,3 | 10-50 |
| 6 | PP-C-003 | 1,2,3 | 10-50 |
| 7 | PP-C-004 | 1,2,3 | 10-50 |

**Note:** DC (id=1) не имеет stock — это распределительный центр.
**Reserved:** 0 для всех записей.

## Файл
`src/main/resources/db/migration/V7__seed_stock.sql`

## Prerequisite
- Products с id 1-5 должны существовать
- Facilities 2-7 созданы (V5)

## Checkpoint
```bash
TOKEN=$(curl -s -X POST http://192.168.1.74:31080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# Stock на WH-C-001 (5 записей)
curl -s http://192.168.1.74:31080/api/stock/facility/2 \
  -H "Authorization: Bearer $TOKEN" | jq '. | length'
# Expected: 5

# Stock на PP-C-001 (3 записи)
curl -s http://192.168.1.74:31080/api/stock/facility/4 \
  -H "Authorization: Bearer $TOKEN" | jq '. | length'
# Expected: 3
```

## Definition of Done
- [ ] V7 миграция создана
- [ ] WH facilities имеют по 5 stock records
- [ ] PP facilities имеют по 3 stock records
- [ ] DC не имеет stock records
- [ ] Все quantity > 0, reserved = 0
```

**Labels:** `flyway`, `backend`, `task`

---

## Task 4: Integration Tests

**Title:** WH-271.4: Integration tests — facility hierarchy

**Body:**
```markdown
## Задача
Создать `FacilityHierarchyIntegrationTest.java` с 4 тестами.

## Тесты
| Test | Описание | Assert |
|------|----------|--------|
| `testFacilityTreeStructure` | GET /tree | 7 facilities, 3 levels |
| `testUserFacilityBinding` | Login operator | JWT contains facility claims |
| `testStockByFacility` | GET /stock/facility/{id} | WH: 5 records, PP: 3 records |
| `testHierarchyNavigation` | Check parent-child | DC→2 WH, WH→2 PP |

## Файл
`src/test/java/com/warehouse/integration/FacilityHierarchyIntegrationTest.java`

## Образец
`StockControllerIntegrationTest.java`

## Checkpoint
```bash
cd ~/warehouse-api
./mvnw test -Dtest=FacilityHierarchyIntegrationTest
# Expected: Tests run: 4, Failures: 0, Errors: 0
```

## Definition of Done
- [ ] 4 теста написаны
- [ ] Все тесты проходят локально
- [ ] CI pipeline зелёный
- [ ] Коммит в develop
```

**Labels:** `testing`, `backend`, `task`

---

## Команды для создания в GitHub CLI

```bash
# Story
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "[Phase 1] WH-271: Test Hierarchy Setup (DC → WH → PP)" \
  --label "phase-1,data-model,story" \
  --body-file wh271_story.md

# Task 1
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "WH-271.1: Flyway V5 — seed facilities (7 records)" \
  --label "flyway,backend,task" \
  --body-file wh271_task1.md

# Task 2
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "WH-271.2: Flyway V6 — seed facility users (7 operators)" \
  --label "flyway,backend,task" \
  --body-file wh271_task2.md

# Task 3
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "WH-271.3: Flyway V7 — seed stock records" \
  --label "flyway,backend,task" \
  --body-file wh271_task3.md

# Task 4
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "WH-271.4: Integration tests — facility hierarchy" \
  --label "testing,backend,task" \
  --body-file wh271_task4.md
```

---

## Порядок выполнения

```
┌─────────────────────────────────────────────────────────┐
│ Task 1: V5 facilities                                    │
│ ├─ Create migration                                      │
│ ├─ Deploy dev                                            │
│ ├─ Verify: GET /api/facilities/tree → 7 records         │
│ └─ ✅ STOP → Report → Approve next                      │
├─────────────────────────────────────────────────────────┤
│ Task 2: V6 users                                         │
│ ├─ Create migration                                      │
│ ├─ Deploy dev                                            │
│ ├─ Verify: Login wh_north_op → JWT with facility        │
│ └─ ✅ STOP → Report → Approve next                      │
├─────────────────────────────────────────────────────────┤
│ Task 3: V7 stock                                         │
│ ├─ Create migration                                      │
│ ├─ Deploy dev                                            │
│ ├─ Verify: GET /stock/facility/2 → 5 records            │
│ └─ ✅ STOP → Report → Approve next                      │
├─────────────────────────────────────────────────────────┤
│ Task 4: Integration tests                                │
│ ├─ Create test class                                     │
│ ├─ Run: ./mvnw test -Dtest=FacilityHierarchy...         │
│ ├─ Verify: 4/4 passed                                    │
│ └─ ✅ Commit all → Push develop → Close story           │
└─────────────────────────────────────────────────────────┘
```