# E2E Testing Guide

Руководство по написанию E2E тестов для Warehouse API.

---

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Структура проекта](#структура-проекта)
3. [Конфигурация](#конфигурация)
4. [Пользователи и роли](#пользователи-и-роли)
5. [Facilities (объекты)](#facilities-объекты)
6. [Написание тестов](#написание-тестов)
7. [Частые ошибки](#частые-ошибки)
8. [Примеры тестов](#примеры-тестов)
9. [Запуск тестов](#запуск-тестов)

---

## Быстрый старт

```bash
cd testing/e2e-tests

# Запуск всех тестов
./mvnw test

# Запуск конкретного теста
./mvnw test -Dtest="ReceiptsApiTest"

# Запуск нескольких тестов
./mvnw test -Dtest="ReceiptsApiTest,ShipmentsApiTest"
```

---

## Структура проекта

```
testing/e2e-tests/
├── src/test/java/com/warehouse/e2e/
│   ├── base/
│   │   └── BaseE2ETest.java      # Базовый класс для всех тестов
│   ├── config/
│   │   └── TestConfig.java       # Конфигурация (URL, credentials)
│   └── tests/
│       ├── ReceiptsApiTest.java
│       ├── ShipmentsApiTest.java
│       ├── IssueActsApiTest.java
│       └── InventoryActsApiTest.java
├── src/test/resources/
│   └── test.properties           # Настройки окружения
└── pom.xml
```

---

## Конфигурация

### test.properties

```properties
# Dev environment (по умолчанию)
base.url=http://192.168.1.74:31080

# Credentials
superuser.username=admin
superuser.password=admin123

admin.username=admin
admin.password=admin123

manager.username=admin
manager.password=admin123

employee.username=wh_north_op
employee.password=password123

analyst.username=pp_1_op
analyst.password=password123
```

### Переопределение через JVM

```bash
./mvnw test -Dbase.url=http://localhost:8080 -Dsuperuser.password=newpass
```

---

## Пользователи и роли

### Доступные роли

| Роль | Описание | Права |
|------|----------|-------|
| `SUPER_USER` | Суперпользователь | Все права |
| `EMPLOYEE` | Сотрудник | Создание/просмотр документов, ship/deliver |
| `MANAGER` | Менеджер | Approve, cancel, delete документов |
| `ADMIN` | Админ | Аналогично MANAGER |

### Тестовые пользователи

| Username | Password | Роль | Facility |
|----------|----------|------|----------|
| `admin` | `admin123` | SUPER_USER | - |
| `dc_central_mgr` | `password123` | EMPLOYEE | DC-C-001 (id=1) |
| `wh_north_op` | `password123` | EMPLOYEE | WH-C-001 (id=2) |
| `wh_south_op` | `password123` | EMPLOYEE | WH-C-002 (id=3) |
| `pp_1_op` | `password123` | EMPLOYEE | PP-C-001 (id=4) |
| `pp_2_op` | `password123` | EMPLOYEE | PP-C-002 (id=5) |

### Важно о ролях

```
В системе только 2 роли: SUPER_USER и EMPLOYEE

- MANAGER в тестах = admin (SUPER_USER имеет все права)
- ANALYST в тестах = pp_1_op (EMPLOYEE с другого facility)
- EMPLOYEE может: создавать документы, ship, deliver, complete
- Только MANAGER/ADMIN могут: approve, cancel, delete
```

---

## Facilities (объекты)

### Типы facilities

| Тип | Описание | Issue Acts | Inventory Acts |
|-----|----------|------------|----------------|
| `DC` | Distribution Center | НЕТ | ДА |
| `WH` | Warehouse | НЕТ | ДА |
| `PP` | Pickup Point (ПВЗ) | ДА | ДА |

### Доступные facilities

| ID | Code | Type | Name |
|----|------|------|------|
| 1 | DC-C-001 | DC | Центральный РЦ |
| 2 | WH-C-001 | WH | Склад Север |
| 3 | WH-C-002 | WH | Склад Юг |
| 4 | PP-C-001 | PP | ПВЗ 1 |
| 5 | PP-C-002 | PP | ПВЗ 2 |
| 6 | PP-C-003 | PP | ПВЗ 3 |
| 7 | PP-C-004 | PP | ПВЗ 4 |

### Правила использования

```java
// Receipt/Shipment - любой facility (DC, WH, PP)
private static final Long TEST_FACILITY_ID = 1L;  // DC-C-001

// Issue Acts - ТОЛЬКО PP!
private static final Long TEST_FACILITY_ID = 4L;  // PP-C-001

// Inventory Acts - любой facility
private static final Long TEST_FACILITY_ID = 2L;  // WH-C-001
```

---

## Написание тестов

### Базовый класс

Все тесты наследуются от `BaseE2ETest`:

```java
public class MyApiTest extends BaseE2ETest {
    // Доступные методы:
    // - request()                    - запрос без авторизации
    // - authRequest(token)           - запрос с токеном
    // - getEmployeeToken()           - токен EMPLOYEE
    // - getManagerToken()            - токен MANAGER (= admin)
    // - getAdminToken()              - токен ADMIN (= admin)
    // - getAnalystToken()            - токен ANALYST (= pp_1_op)
    // - getSuperuserToken()          - токен SUPER_USER
    // - extractLong(value)           - безопасное преобразование в Long
}
```

### Структура теста

```java
@Epic("Warehouse API")
@Feature("My Feature")
@DisplayName("My API Tests")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class MyApiTest extends BaseE2ETest {

    private static Long createdId;
    private static final Long TEST_FACILITY_ID = 1L;
    private static final Long TEST_PRODUCT_ID = 1L;

    @Test
    @Order(10)
    @Story("Create")
    @Severity(SeverityLevel.BLOCKER)
    @DisplayName("Создание документа")
    void createDocument() {
        // Test implementation
    }
}
```

---

## Частые ошибки

### 1. Integer/Long casting

**Проблема:** REST-assured возвращает Integer для JSON чисел

```java
// НЕПРАВИЛЬНО - ClassCastException!
Long id = response.path("id");

// ПРАВИЛЬНО - используй extractLong()
Long id = extractLong(response.path("id"));
```

### 2. Неверный facility для Issue Acts

**Проблема:** Issue Acts только для PP (Pickup Points)

```java
// НЕПРАВИЛЬНО - 400 Bad Request
private static final Long TEST_FACILITY_ID = 1L;  // DC

// ПРАВИЛЬНО
private static final Long TEST_FACILITY_ID = 4L;  // PP-C-001
```

### 3. Тесты на 403 для ANALYST

**Проблема:** ANALYST = EMPLOYEE, имеет права на создание документов

```java
// НЕПРАВИЛЬНО - тест упадёт (получим 201, не 403)
@Test
void analystCannotCreateDocument() {
    authRequest(getAnalystToken())
        .body(...)
        .post("/api/receipts")
        .then()
        .statusCode(403);  // FAIL! Получим 201
}

// Какие операции ANALYST (EMPLOYEE) НЕ может делать:
// - approve (требует MANAGER)
// - cancel (требует MANAGER)
// - delete (требует MANAGER)
```

### 4. Сравнение ID в response body

**Проблема:** JSON возвращает Integer, Java ожидает Long

```java
// НЕПРАВИЛЬНО - может упасть
.body("id", equalTo(createdId))

// ПРАВИЛЬНО
.body("id", equalTo(createdId.intValue()))
```

### 5. Неверные credentials

**Проблема:** Использование несуществующих пользователей

```java
// Реальные пользователи в системе:
// admin / admin123
// wh_north_op / password123
// pp_1_op / password123

// НЕ существуют:
// manager / manager123
// analyst / analyst123
```

---

## Примеры тестов

### Пример 1: CRUD тест

```java
@Test
@Order(10)
@Story("Create Receipt")
@Severity(SeverityLevel.BLOCKER)
@DisplayName("EMPLOYEE создаёт Receipt в статусе DRAFT")
void employeeCreatesReceiptDraft() {
    var response = authRequest(getEmployeeToken())
        .body(Map.of(
            "facilityId", TEST_FACILITY_ID,
            "supplierId", 1L,
            "notes", "E2E Test Receipt",
            "items", List.of(
                Map.of("productId", TEST_PRODUCT_ID, "quantity", 100)
            )
        ))
    .when()
        .post("/api/receipts")
    .then()
        .statusCode(201)
        .body("id", notNullValue())
        .body("status", equalTo("DRAFT"))
        .body("facilityId", equalTo(TEST_FACILITY_ID.intValue()))
        .body("items", hasSize(1))
        .extract();

    // Сохраняем ID для следующих тестов
    createdReceiptId = extractLong(response.path("id"));
    Allure.attachment("Created Receipt ID", String.valueOf(createdReceiptId));
}
```

### Пример 2: State Machine тест

```java
@Test
@Order(70)
@Story("State Machine")
@Severity(SeverityLevel.BLOCKER)
@DisplayName("Полный цикл: DRAFT → APPROVED → CONFIRMED → COMPLETED")
void fullStateMachineCycle() {
    // 1. Создаём DRAFT
    Long receiptId = extractLong(authRequest(getEmployeeToken())
        .body(Map.of(
            "facilityId", TEST_FACILITY_ID,
            "supplierId", 1L,
            "items", List.of(Map.of("productId", TEST_PRODUCT_ID, "quantity", 50))
        ))
    .when()
        .post("/api/receipts")
    .then()
        .statusCode(201)
        .body("status", equalTo("DRAFT"))
        .extract()
        .path("id"));

    // 2. Утверждаем DRAFT → APPROVED (требует MANAGER)
    authRequest(getManagerToken())
    .when()
        .post("/api/receipts/" + receiptId + "/approve")
    .then()
        .statusCode(200)
        .body("status", equalTo("APPROVED"));

    // 3. Подтверждаем APPROVED → CONFIRMED (EMPLOYEE может)
    authRequest(getEmployeeToken())
    .when()
        .post("/api/receipts/" + receiptId + "/confirm")
    .then()
        .statusCode(200)
        .body("status", equalTo("CONFIRMED"));

    // 4. Завершаем CONFIRMED → COMPLETED (EMPLOYEE может)
    authRequest(getEmployeeToken())
    .when()
        .post("/api/receipts/" + receiptId + "/complete")
    .then()
        .statusCode(200)
        .body("status", equalTo("COMPLETED"));

    Allure.attachment("Full Cycle Receipt ID", String.valueOf(receiptId));
}
```

### Пример 3: Тест на запрет доступа

```java
@Test
@Order(31)
@Story("Approve Receipt")
@Severity(SeverityLevel.CRITICAL)
@DisplayName("EMPLOYEE НЕ может утверждать Receipt (403)")
void employeeCannotApproveReceipt() {
    // Создаём Receipt
    Long receiptId = extractLong(authRequest(getEmployeeToken())
        .body(Map.of(
            "facilityId", TEST_FACILITY_ID,
            "supplierId", 1L,
            "items", List.of(Map.of("productId", TEST_PRODUCT_ID, "quantity", 10))
        ))
    .when()
        .post("/api/receipts")
    .then()
        .statusCode(201)
        .extract()
        .path("id"));

    // Пытаемся утвердить как EMPLOYEE - должен быть 403
    authRequest(getEmployeeToken())
    .when()
        .post("/api/receipts/" + receiptId + "/approve")
    .then()
        .statusCode(403);

    // Cleanup - удаляем через MANAGER
    authRequest(getManagerToken())
        .when().post("/api/receipts/" + receiptId + "/cancel");
}
```

### Пример 4: Тест без авторизации

```java
@Test
@Order(23)
@Story("Get Receipt")
@Severity(SeverityLevel.CRITICAL)
@DisplayName("Получение Receipt без токена возвращает 403")
void getReceiptWithoutToken() {
    request()  // без токена!
    .when()
        .get("/api/receipts/1")
    .then()
        .statusCode(403);
}
```

### Пример 5: Валидация ошибок

```java
@Test
@Order(16)
@Story("Create Receipt")
@Severity(SeverityLevel.NORMAL)
@DisplayName("Создание Receipt без items возвращает 400")
void createReceiptWithoutItems() {
    authRequest(getEmployeeToken())
        .body(Map.of(
            "facilityId", TEST_FACILITY_ID,
            "supplierId", 1L,
            "items", List.of()  // Пустой список
        ))
    .when()
        .post("/api/receipts")
    .then()
        .statusCode(400);
}
```

---

## Запуск тестов

### Локально

```bash
cd testing/e2e-tests

# Все тесты
./mvnw test

# Конкретный класс
./mvnw test -Dtest="ReceiptsApiTest"

# Несколько классов
./mvnw test -Dtest="ReceiptsApiTest,ShipmentsApiTest"

# С другим URL
./mvnw test -Dbase.url=http://localhost:8080

# С отчётом Allure
./mvnw test allure:serve
```

### Allure отчёты

```bash
# Генерация отчёта
./mvnw allure:report

# Открыть в браузере
./mvnw allure:serve
```

---

## Чек-лист перед написанием теста

- [ ] Выбран правильный `TEST_FACILITY_ID` для типа документа
- [ ] Используется `extractLong()` для извлечения ID
- [ ] ID сравнивается через `.intValue()` в body assertions
- [ ] Cleanup создаёт документы от того же или выше уровня доступа
- [ ] Тесты на 403 проверяют только операции, реально требующие MANAGER
- [ ] Порядок тестов (@Order) учитывает зависимости
- [ ] Allure аннотации добавлены (@Epic, @Feature, @Story, @Severity)

---

## API Reference

### State Machines

```
Receipt:   DRAFT → APPROVED → CONFIRMED → COMPLETED
           └──────────────→ CANCELLED

Shipment:  DRAFT → APPROVED → SHIPPED → DELIVERED
           └──────────────→ CANCELLED

IssueAct:  DRAFT → COMPLETED

Inventory: DRAFT → APPROVED → COMPLETED
```

### Endpoints

| Документ | Base Path | Create | Approve | Complete | Delete |
|----------|-----------|--------|---------|----------|--------|
| Receipt | /api/receipts | POST / | POST /{id}/approve | POST /{id}/complete | POST /{id}/cancel |
| Shipment | /api/shipments | POST / | POST /{id}/approve | POST /{id}/deliver | POST /{id}/cancel |
| IssueAct | /api/issue-acts | POST / | - | POST /{id}/complete | DELETE /{id} |
| Inventory | /api/inventory-acts | POST / | - | POST /{id}/complete | DELETE /{id} |

### Права по операциям

| Операция | EMPLOYEE | MANAGER/ADMIN |
|----------|----------|---------------|
| Create | ✅ | ✅ |
| View | ✅ | ✅ |
| Approve | ❌ | ✅ |
| Confirm | ✅ | ✅ |
| Ship/Deliver | ✅ | ✅ |
| Complete | ✅ | ✅ |
| Cancel | ❌ | ✅ |
| Delete | ❌ | ✅ |

---

*Обновлено: 2025-12-12*
