# Фаза 2: Документооборот — Инструкция для агента

## Обзор

4 story, выполняются последовательно. Каждый блок — остановка, отчёт, подтверждение.

```
WH-272: Receipt Documents (приход)
    ↓
WH-273: Shipment Documents (расход)  
    ↓
WH-274: Kafka Auto-Documents (автоматизация)
    ↓
WH-275: Issue & Inventory Acts (выдача + инвентаризация)
```

---

## Общие паттерны

### Document State Machines

```
Receipt:   DRAFT → APPROVED → CONFIRMED → COMPLETED
Shipment:  DRAFT → APPROVED → SHIPPED → DELIVERED
IssueAct:  DRAFT → COMPLETED (instant)
Inventory: DRAFT → APPROVED → COMPLETED
```

### Нумерация документов

| Тип | Формат | Пример |
|-----|--------|--------|
| Receipt | RCP-{facilityCode}-{YYYYMMDD}-{seq} | RCP-WH-C-001-20251211-001 |
| Shipment | SHP-{facilityCode}-{YYYYMMDD}-{seq} | SHP-WH-C-001-20251211-001 |
| IssueAct | ISS-{facilityCode}-{YYYYMMDD}-{seq} | ISS-PP-C-001-20251211-001 |
| Inventory | INV-{facilityCode}-{YYYYMMDD}-{seq} | INV-WH-C-001-20251211-001 |

### Образцы в проекте

| Паттерн | Файл |
|---------|------|
| Entity | Stock.java, Facility.java |
| Controller | StockController.java |
| Service | StockService.java, FacilityService.java |
| Repository | StockRepository.java |
| DTO | StockDTO.java, FacilityResponse.java |
| Flyway | V4__add_stock_table.sql |
| Enum | ReceiptStatus.java, FacilityType.java |

### Текущая версия Flyway: V7

---

# WH-272: Receipt Documents (Приходные накладные)

## Цель
Документ прихода товара на объект. При CONFIRMED — увеличивает stock.

---

## Блок 1: Entity + Migration (WH-305, WH-306)

### Файлы создать

| Файл | Путь |
|------|------|
| V8__add_receipt_documents.sql | src/main/resources/db/migration/ |
| ReceiptStatus.java | src/main/java/com/warehouse/model/ |
| ReceiptDocument.java | src/main/java/com/warehouse/model/ |
| ReceiptItem.java | src/main/java/com/warehouse/model/ |

### Таблица receipt_documents

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PRIMARY KEY |
| document_number | VARCHAR(50) | NOT NULL UNIQUE |
| facility_id | BIGINT | NOT NULL REFERENCES facilities(id) |
| supplier_name | VARCHAR(255) | - |
| status | VARCHAR(20) | NOT NULL DEFAULT 'DRAFT' |
| notes | TEXT | - |
| created_by | BIGINT | REFERENCES users(id) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| approved_at | TIMESTAMP | - |
| approved_by | BIGINT | REFERENCES users(id) |
| confirmed_at | TIMESTAMP | - |
| confirmed_by | BIGINT | REFERENCES users(id) |

### Таблица receipt_items

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PRIMARY KEY |
| receipt_id | BIGINT | NOT NULL REFERENCES receipt_documents(id) ON DELETE CASCADE |
| product_id | BIGINT | NOT NULL REFERENCES products(id) |
| expected_quantity | INTEGER | NOT NULL CHECK > 0 |
| actual_quantity | INTEGER | DEFAULT 0, CHECK >= 0 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### ReceiptStatus enum

```
DRAFT, APPROVED, CONFIRMED, COMPLETED
```

### Entity связи

- ReceiptDocument → Facility (ManyToOne)
- ReceiptDocument → User (createdBy, approvedBy, confirmedBy)
- ReceiptDocument → List<ReceiptItem> (OneToMany, cascade ALL)
- ReceiptItem → ReceiptDocument (ManyToOne)
- ReceiptItem → Product (ManyToOne)

**Образец:** Stock.java (entity с связями), V4__add_stock_table.sql (миграция)

### Checkpoint Блок 1

```bash
# Deploy и проверить таблицы
kubectl exec -n warehouse-dev deployment/warehouse-api -- \
  psql -U warehouse_user -d warehouse_dev -c "\dt receipt*"
# Expected: receipt_documents, receipt_items
```

**✅ STOP → Report → Approve next**

---

## Блок 2: Repository + DTO (WH-308)

### Файлы создать

| Файл | Путь |
|------|------|
| ReceiptDocumentRepository.java | src/main/java/com/warehouse/repository/ |
| ReceiptDocumentDTO.java | src/main/java/com/warehouse/dto/ |
| ReceiptItemDTO.java | src/main/java/com/warehouse/dto/ |
| ReceiptCreateRequest.java | src/main/java/com/warehouse/dto/ |
| ReceiptConfirmRequest.java | src/main/java/com/warehouse/dto/ |

### Repository методы

| Method | Description |
|--------|-------------|
| findByFacilityId(Long) | Документы по объекту |
| findByFacilityIdAndStatus(Long, Status) | По объекту и статусу |
| countByFacilityAndDate(Long, LocalDateTime, LocalDateTime) | Для генерации номера |
| findByIdWithItems(Long) | С позициями (JOIN FETCH) |

### ReceiptDocumentDTO поля

| Field | Type |
|-------|------|
| id | Long |
| documentNumber | String |
| facilityId, facilityCode, facilityName | Long, String, String |
| supplierName | String |
| status | ReceiptStatus |
| notes | String |
| createdAt, createdByUsername | LocalDateTime, String |
| approvedAt, approvedByUsername | LocalDateTime, String |
| confirmedAt, confirmedByUsername | LocalDateTime, String |
| items | List<ReceiptItemDTO> |
| totalExpected, totalActual | Integer, Integer |

### ReceiptItemDTO поля

| Field | Type |
|-------|------|
| id | Long |
| productId, productName | Long, String |
| expectedQuantity | Integer |
| actualQuantity | Integer |

### ReceiptCreateRequest поля

| Field | Validation |
|-------|------------|
| facilityId | @NotNull |
| supplierName | - |
| notes | - |
| items | @NotNull @Size(min=1), List of {productId, expectedQuantity} |

### ReceiptConfirmRequest поля

| Field | Description |
|-------|-------------|
| items | List of {itemId, actualQuantity} |

**Образец:** StockDTO.java, FacilityCreateRequest.java

### Checkpoint Блок 2

```bash
./mvnw compile
# Expected: BUILD SUCCESS
```

**✅ STOP → Report → Approve next**

---

## Блок 3: Service — State Machine (WH-307, WH-309, WH-310)

### Файл создать

| Файл | Путь |
|------|------|
| ReceiptDocumentService.java | src/main/java/com/warehouse/service/ |

### Методы

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| create(ReceiptCreateRequest, User) | request, currentUser | ReceiptDocumentDTO | Создать DRAFT |
| getById(Long) | id | ReceiptDocumentDTO | Получить с items |
| getByFacility(Long) | facilityId | List<DTO> | Все по объекту |
| approve(Long, User) | id, currentUser | ReceiptDocumentDTO | DRAFT → APPROVED |
| confirm(Long, ReceiptConfirmRequest, User) | id, actualQty, user | ReceiptDocumentDTO | APPROVED → CONFIRMED + **stock update** |
| complete(Long) | id | ReceiptDocumentDTO | CONFIRMED → COMPLETED |
| delete(Long) | id | void | Только DRAFT |

### State Machine правила

| Transition | Условие | Действие |
|------------|---------|----------|
| DRAFT → APPROVED | Есть items | Set approvedAt, approvedBy |
| APPROVED → CONFIRMED | actualQuantity заполнен | Set confirmedAt, confirmedBy, **UPDATE STOCK** |
| CONFIRMED → COMPLETED | - | Финальный статус |

### Stock Update логика (на CONFIRMED)

```
Для каждого item:
  stock = findOrCreate(productId, facilityId)
  stock.quantity += item.actualQuantity
  save(stock)
  auditService.log("RECEIPT_CONFIRMED", ...)
```

### Генерация номера документа

```
Format: RCP-{facilityCode}-{YYYYMMDD}-{seq}
seq = countByFacilityAndDate() + 1, padded to 3 digits
Example: RCP-WH-C-001-20251211-001
```

**Образец:** StockService.java (транзакции, audit), FacilityService.java (генерация кода)

### Checkpoint Блок 3

```bash
./mvnw compile
# Expected: BUILD SUCCESS
```

**✅ STOP → Report → Approve next**

---

## Блок 4: Controller (WH-311)

### Файл создать

| Файл | Путь |
|------|------|
| ReceiptDocumentController.java | src/main/java/com/warehouse/controller/ |

### Endpoints

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| POST | /api/receipts | EMPLOYEE+ | Создать документ |
| GET | /api/receipts/{id} | EMPLOYEE+ | Получить по ID |
| GET | /api/receipts/facility/{facilityId} | EMPLOYEE+ | По объекту |
| POST | /api/receipts/{id}/approve | MANAGER+ | DRAFT → APPROVED |
| POST | /api/receipts/{id}/confirm | EMPLOYEE+ | APPROVED → CONFIRMED |
| POST | /api/receipts/{id}/complete | MANAGER+ | CONFIRMED → COMPLETED |
| DELETE | /api/receipts/{id} | MANAGER+ | Удалить DRAFT |

**Образец:** StockController.java

### Checkpoint Блок 4

```bash
TOKEN=$(curl -s -X POST http://192.168.1.74:31080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# Создать Receipt
curl -s -X POST http://192.168.1.74:31080/api/receipts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"facilityId":2,"supplierName":"Test Supplier","items":[{"productId":1,"expectedQuantity":100}]}' | jq

# Expected: status=DRAFT, documentNumber=RCP-WH-C-001-...
```

**✅ STOP → Report → Approve next**

---

## Блок 5: Unit Tests (WH-312)

### Файл создать

| Файл | Путь |
|------|------|
| ReceiptDocumentServiceTest.java | src/test/java/com/warehouse/service/ |
| ReceiptDocumentControllerTest.java | src/test/java/com/warehouse/controller/ |

### Тесты Service

| Test | Description |
|------|-------------|
| testCreateReceipt_Valid | Создание с items |
| testCreateReceipt_EmptyItems | Ошибка без items |
| testApprove_FromDraft | DRAFT → APPROVED |
| testApprove_NotDraft | Ошибка если не DRAFT |
| testConfirm_UpdatesStock | Stock увеличивается |
| testConfirm_NotApproved | Ошибка если не APPROVED |
| testDelete_OnlyDraft | Удаление только DRAFT |
| testGenerateDocumentNumber | Формат номера |

### Тесты Controller

| Test | Description |
|------|-------------|
| testCreateReceipt_Authorized | 201 Created |
| testCreateReceipt_Unauthorized | 401/403 |
| testGetByFacility_ReturnsList | Список по объекту |
| testApprove_ManagerOnly | Проверка роли |

**Образец:** StockControllerTest.java (если есть), или паттерн Spring MockMvc

### Checkpoint Блок 5

```bash
./mvnw test -Dtest=ReceiptDocument*
# Expected: Tests passed
```

**✅ STOP → Report → Approve next → WH-272 DONE**

---

# WH-273: Shipment Documents (Расходные накладные)

## Цель
Документ отгрузки товара с объекта. При APPROVED — резервирует stock. При SHIPPED — списывает.

---

## Блок 1: Entity + Migration (WH-313, WH-314)

### Файлы создать

| Файл | Путь |
|------|------|
| V9__add_shipment_documents.sql | src/main/resources/db/migration/ |
| ShipmentStatus.java | src/main/java/com/warehouse/model/ |
| ShipmentDocument.java | src/main/java/com/warehouse/model/ |
| ShipmentItem.java | src/main/java/com/warehouse/model/ |

### Таблица shipment_documents

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PRIMARY KEY |
| document_number | VARCHAR(50) | NOT NULL UNIQUE |
| source_facility_id | BIGINT | NOT NULL REFERENCES facilities(id) |
| destination_facility_id | BIGINT | REFERENCES facilities(id) |
| destination_address | VARCHAR(500) | Если внешний адрес |
| status | VARCHAR(20) | NOT NULL DEFAULT 'DRAFT' |
| notes | TEXT | - |
| created_by, created_at | BIGINT, TIMESTAMP | - |
| approved_by, approved_at | BIGINT, TIMESTAMP | - |
| shipped_by, shipped_at | BIGINT, TIMESTAMP | - |
| delivered_at | TIMESTAMP | - |

### Таблица shipment_items

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PRIMARY KEY |
| shipment_id | BIGINT | NOT NULL REFERENCES shipment_documents(id) ON DELETE CASCADE |
| product_id | BIGINT | NOT NULL REFERENCES products(id) |
| quantity | INTEGER | NOT NULL CHECK > 0 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### ShipmentStatus enum

```
DRAFT, APPROVED, SHIPPED, DELIVERED
```

**Образец:** V8__add_receipt_documents.sql

### Checkpoint Блок 1

```bash
kubectl exec -n warehouse-dev deployment/warehouse-api -- \
  psql -U warehouse_user -d warehouse_dev -c "\dt shipment*"
# Expected: shipment_documents, shipment_items
```

**✅ STOP → Report → Approve next**

---

## Блок 2: Repository + DTO (WH-316)

### Файлы создать

| Файл | Описание |
|------|----------|
| ShipmentDocumentRepository.java | CRUD + поиск |
| ShipmentDocumentDTO.java | Response DTO |
| ShipmentItemDTO.java | Item DTO |
| ShipmentCreateRequest.java | Create request |

### ShipmentDocumentDTO поля

| Field | Type |
|-------|------|
| id, documentNumber | Long, String |
| sourceFacilityId, sourceFacilityCode | Long, String |
| destinationFacilityId, destinationFacilityCode | Long, String |
| destinationAddress | String |
| status | ShipmentStatus |
| items | List<ShipmentItemDTO> |
| totalQuantity | Integer |
| timestamps, usernames | ... |

**Образец:** ReceiptDocumentDTO.java

### Checkpoint Блок 2

```bash
./mvnw compile
```

**✅ STOP → Report → Approve next**

---

## Блок 3: Service — Reserve + Ship (WH-317, WH-318, WH-319)

### ShipmentDocumentService методы

| Method | Description |
|--------|-------------|
| create(request, user) | Создать DRAFT |
| approve(id, user) | DRAFT → APPROVED, **RESERVE stock** |
| ship(id, user) | APPROVED → SHIPPED, **DEDUCT stock** |
| deliver(id) | SHIPPED → DELIVERED |
| cancel(id) | DRAFT/APPROVED → отмена, **RELEASE reserve** |

### Stock Operations

| Transition | Stock Action |
|------------|--------------|
| APPROVED | stock.reserved += quantity (проверить available >= quantity) |
| SHIPPED | stock.quantity -= quantity, stock.reserved -= quantity |
| CANCEL (если APPROVED) | stock.reserved -= quantity |

**Образец:** StockService.java (reserve, ship методы уже есть)

### Checkpoint Блок 3

```bash
./mvnw compile
```

**✅ STOP → Report → Approve next**

---

## Блок 4: Controller (WH-320)

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/shipments | Создать |
| GET | /api/shipments/{id} | Получить |
| GET | /api/shipments/facility/{id} | По объекту |
| POST | /api/shipments/{id}/approve | → APPROVED (reserve) |
| POST | /api/shipments/{id}/ship | → SHIPPED (deduct) |
| POST | /api/shipments/{id}/deliver | → DELIVERED |
| POST | /api/shipments/{id}/cancel | Отмена |

### Checkpoint Блок 4

```bash
# Создать Shipment
curl -s -X POST http://192.168.1.74:31080/api/shipments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sourceFacilityId":2,"destinationFacilityId":4,"items":[{"productId":1,"quantity":10}]}' | jq

# Approve (reserve stock)
curl -s -X POST http://192.168.1.74:31080/api/shipments/1/approve \
  -H "Authorization: Bearer $TOKEN" | jq

# Check stock reserved
curl -s http://192.168.1.74:31080/api/stock/product/1/facility/2 \
  -H "Authorization: Bearer $TOKEN" | jq '.reserved'
# Expected: 10
```

**✅ STOP → Report → Approve next**

---

## Блок 5: Unit Tests (WH-321)

### Тесты

| Test | Description |
|------|-------------|
| testApprove_ReservesStock | reserved увеличивается |
| testApprove_InsufficientStock | Ошибка если available < quantity |
| testShip_DeductsStock | quantity и reserved уменьшаются |
| testCancel_ReleasesReserve | reserved уменьшается |
| testDeliver_FinalState | Статус DELIVERED |

### Checkpoint Блок 5

```bash
./mvnw test -Dtest=ShipmentDocument*
```

**✅ STOP → Report → Approve next → WH-273 DONE**

---

# WH-274: Kafka Auto-Documents

## Цель
При SHIPPED shipment автоматически создаётся Receipt на destination facility.

---

## Блок 1: Kafka Topics (WH-322, WH-323)

### Topics создать

| Topic | Partitions | Purpose |
|-------|------------|---------|
| logistics.shipments | 3 | Shipment events |
| logistics.receipts | 3 | Receipt events |

### Kafka config (уже есть KafkaConfig.java)

Добавить topics в конфигурацию или создать через CLI.

**Образец:** warehouse.audit topic

### Checkpoint Блок 1

```bash
kubectl exec -n warehouse-dev deployment/kafka -- \
  kafka-topics.sh --list --bootstrap-server localhost:9092 | grep logistics
# Expected: logistics.shipments, logistics.receipts
```

**✅ STOP → Report → Approve next**

---

## Блок 2: Events + Producer (WH-324)

### Файлы создать

| Файл | Путь |
|------|------|
| ShipmentEvent.java | src/main/java/com/warehouse/dto/ |
| LogisticsEventProducer.java | src/main/java/com/warehouse/service/ |

### ShipmentEvent поля

| Field | Type |
|-------|------|
| eventType | String (DISPATCHED, DELIVERED) |
| shipmentId | Long |
| documentNumber | String |
| sourceFacilityId | Long |
| destinationFacilityId | Long |
| items | List<{productId, quantity}> |
| timestamp | LocalDateTime |

### Producer логика

При ShipmentService.ship() → отправить SHIPMENT_DISPATCHED в logistics.shipments

**Образец:** AuditService.java (Kafka producer)

### Checkpoint Блок 2

```bash
# Ship и проверить Kafka
kubectl exec -n warehouse-dev deployment/kafka -- \
  kafka-console-consumer.sh --topic logistics.shipments \
  --bootstrap-server localhost:9092 --from-beginning --max-messages 1
```

**✅ STOP → Report → Approve next**

---

## Блок 3: Consumer — Auto Receipt (WH-325)

### Файл создать

| Файл | Путь |
|------|------|
| LogisticsEventConsumer.java | src/main/java/com/warehouse/service/ |

### Consumer логика

```
On SHIPMENT_DISPATCHED:
  1. Найти destination facility
  2. Создать ReceiptDocument (status=DRAFT или APPROVED)
  3. Скопировать items из shipment
  4. Сохранить связь shipmentId → receiptId
```

### Checkpoint Блок 3

```bash
# Создать shipment DC→WH, ship
# Проверить auto-created receipt на WH
curl -s http://192.168.1.74:31080/api/receipts/facility/2 \
  -H "Authorization: Bearer $TOKEN" | jq '.[0]'
# Expected: supplierName содержит shipment reference
```

**✅ STOP → Report → Approve next**

---

## Блок 4: Receipt Confirmed → Shipment Delivered (WH-326, WH-327)

### Логика

```
On ReceiptService.confirm():
  1. Если receipt связан с shipment
  2. Отправить RECEIPT_CONFIRMED в logistics.receipts
  3. Consumer обновляет Shipment → DELIVERED
```

### Checkpoint Блок 4

```bash
# Confirm receipt
# Check original shipment status = DELIVERED
```

**✅ STOP → Report → Approve next**

---

## Блок 5: Integration Tests (WH-328)

### Тесты

| Test | Description |
|------|-------------|
| testShipmentCreatesReceipt | Ship → auto Receipt created |
| testReceiptConfirmUpdatesShipment | Confirm → Shipment DELIVERED |
| testEndToEndFlow | DC → WH full cycle |

### Checkpoint Блок 5

```bash
./mvnw test -Dtest=LogisticsIntegration*
```

**✅ STOP → Report → Approve next → WH-274 DONE**

---

# WH-275: Issue & Inventory Acts

## Цель
IssueAct — выдача клиенту в ПВЗ (instant stock deduction).
InventoryAct — инвентаризация (stock correction).

---

## Блок 1: IssueAct Entity + Migration (WH-329, WH-330, WH-331)

### V10__add_issue_acts.sql

### Таблица issue_acts

| Column | Type |
|--------|------|
| id | BIGSERIAL |
| document_number | VARCHAR(50) UNIQUE |
| facility_id | BIGINT (только PP!) |
| customer_name | VARCHAR(255) |
| customer_phone | VARCHAR(50) |
| status | VARCHAR(20) (DRAFT, COMPLETED) |
| created_by, created_at | ... |
| completed_at | TIMESTAMP |

### Таблица issue_act_items

| Column | Type |
|--------|------|
| id | BIGSERIAL |
| issue_act_id | BIGINT |
| product_id | BIGINT |
| quantity | INTEGER |

### Логика

- Только для PP (pickup points)
- При COMPLETED — instant stock deduction (не через reserve)
- Простой flow: DRAFT → COMPLETED

### Checkpoint Блок 1

```bash
# Tables created
\dt issue*
```

**✅ STOP → Report → Approve next**

---

## Блок 2: IssueAct Service + Controller (WH-332)

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/issue-acts | Создать |
| GET | /api/issue-acts/{id} | Получить |
| GET | /api/issue-acts/facility/{id} | По ПВЗ |
| POST | /api/issue-acts/{id}/complete | DRAFT → COMPLETED + stock deduction |

### Checkpoint Блок 2

```bash
# Create and complete issue act
curl -X POST .../api/issue-acts/1/complete
# Check stock decreased
```

**✅ STOP → Report → Approve next**

---

## Блок 3: InventoryAct Entity + Migration (WH-333, WH-334)

### V11__add_inventory_acts.sql

### Таблица inventory_acts

| Column | Type |
|--------|------|
| id | BIGSERIAL |
| document_number | VARCHAR(50) |
| facility_id | BIGINT |
| status | VARCHAR(20) (DRAFT, APPROVED, COMPLETED) |
| notes | TEXT |
| created_by, approved_by | ... |

### Таблица inventory_act_items

| Column | Type |
|--------|------|
| id | BIGSERIAL |
| inventory_act_id | BIGINT |
| product_id | BIGINT |
| expected_quantity | INTEGER (из stock) |
| actual_quantity | INTEGER (фактический) |
| difference | INTEGER (computed) |

### Checkpoint Блок 3

```bash
\dt inventory*
```

**✅ STOP → Report → Approve next**

---

## Блок 4: InventoryAct Service + Controller (WH-335, WH-336)

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/inventory-acts | Создать (копирует текущий stock) |
| GET | /api/inventory-acts/{id} | Получить |
| PUT | /api/inventory-acts/{id}/items | Обновить actual quantities |
| POST | /api/inventory-acts/{id}/approve | DRAFT → APPROVED |
| POST | /api/inventory-acts/{id}/complete | APPROVED → COMPLETED + stock correction |

### Stock Correction логика

```
На COMPLETED:
  Для каждого item:
    difference = actual - expected
    stock.quantity += difference (может быть отрицательным)
```

### Checkpoint Блок 4

```bash
# Create inventory, set actual, complete
# Verify stock corrected
```

**✅ STOP → Report → Approve next**

---

## Блок 5: Unit Tests (WH-337)

### Тесты

| Test | Description |
|------|-------------|
| testIssueAct_DeductsStock | Stock уменьшается при complete |
| testIssueAct_OnlyPP | Ошибка для DC/WH |
| testInventory_PositiveDifference | Stock увеличивается |
| testInventory_NegativeDifference | Stock уменьшается |
| testInventory_ZeroDifference | Stock без изменений |

### Checkpoint Блок 5

```bash
./mvnw test -Dtest=IssueAct*,InventoryAct*
```

**✅ STOP → Report → WH-275 DONE → ФАЗА 2 COMPLETE**

---

# Порядок выполнения (Summary)

```
WH-272 Receipt Documents
├── Блок 1: V8 migration + entities
├── Блок 2: Repository + DTO
├── Блок 3: Service (state machine)
├── Блок 4: Controller (7 endpoints)
└── Блок 5: Tests

WH-273 Shipment Documents
├── Блок 1: V9 migration + entities
├── Блок 2: Repository + DTO
├── Блок 3: Service (reserve + ship)
├── Блок 4: Controller (7 endpoints)
└── Блок 5: Tests

WH-274 Kafka Auto-Documents
├── Блок 1: Topics
├── Блок 2: Events + Producer
├── Блок 3: Consumer (auto receipt)
├── Блок 4: Receipt→Shipment link
└── Блок 5: Integration tests

WH-275 Issue & Inventory
├── Блок 1: IssueAct V10 + entities
├── Блок 2: IssueAct service + controller
├── Блок 3: InventoryAct V11 + entities
├── Блок 4: InventoryAct service + controller
└── Блок 5: Tests
```

---

# Критерии готовности Фазы 2

- [ ] 4 типа документов работают
- [ ] State machines корректны
- [ ] Stock обновляется при confirm/ship/complete
- [ ] Kafka auto-documents работают
- [ ] Все тесты проходят
- [ ] Dev environment (31080) работает

---

*Next Action: WH-272 Блок 1 — V8__add_receipt_documents.sql*