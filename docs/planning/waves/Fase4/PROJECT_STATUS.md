# Warehouse Project — Status (2025-12-12)

## Сводка

| Фаза | Название | Статус |
|------|----------|--------|
| 0 | Инфраструктура | ✅ |
| 1 | Модель данных | ✅ |
| 2 | Документооборот | ✅ |
| 3 | Frontend | ✅ |
| 4 | Интеграция (E2E) | 🔄 NEXT |

**Прогресс: 80%** — осталась фаза E2E тестирования

---

## Монорепо структура

```
WaregouseHub/
├── api/                    # Java 17 + Spring Boot 3.2
│   ├── src/main/java/com/warehouse/
│   │   ├── model/          # 21 entities
│   │   ├── repository/     # 9 repositories
│   │   ├── service/        # 17 services
│   │   ├── controller/     # 9 controllers
│   │   └── dto/            # 27 DTOs
│   └── src/main/resources/db/migration/  # V2-V13
│
├── frontend/               # Vue.js 3.4 + Vite 5
│   └── src/
│       ├── components/     # 11 components
│       ├── views/          # 22 views (dc/, wh/, pp/)
│       ├── stores/         # Pinia (facility)
│       ├── composables/    # useDocument, useFormValidation
│       └── assets/         # facility-themes.css
│
├── testing/                # E2E, UI, Load tests
├── k8s/                    # Kubernetes manifests
├── telegram-bot/           # Notification bot
├── analytics-service/      # Kafka consumer
└── docs/                   # Documentation
```

---

## API Summary

### Flyway Migrations (12)

| Version | Purpose |
|---------|---------|
| V2 | add_facilities |
| V3 | add_notifications |
| V4 | add_stock_table |
| V5 | seed_facilities (7 объектов) |
| V6 | seed_facility_users (7 операторов) |
| V7 | seed_stock |
| V8 | add_receipt_documents |
| V9 | add_shipment_documents |
| V10 | link_shipment_receipt |
| V11 | add_issue_acts |
| V12 | add_inventory_acts |
| V13 | fix_password_hashes |

### Models (21)

| Category | Entities |
|----------|----------|
| Core | User, Role, Product |
| Facility | Facility, FacilityType |
| Stock | Stock |
| Notifications | Notification, NotificationChannel, NotificationStatus |
| Receipt | ReceiptDocument, ReceiptItem, ReceiptStatus |
| Shipment | ShipmentDocument, ShipmentItem, ShipmentStatus |
| Issue | IssueAct, IssueActItem, IssueStatus |
| Inventory | InventoryAct, InventoryActItem, InventoryStatus |

### Controllers (9) — 51 endpoints

| Controller | Endpoints |
|------------|-----------|
| AuthController | 4 |
| ProductController | 5 |
| FacilityController | 8 |
| StockController | 8 |
| NotificationController | 3 |
| ReceiptDocumentController | 7 |
| ShipmentDocumentController | 7 |
| IssueActController | 4 |
| InventoryActController | 5 |

### Services (17)

| Service | Purpose |
|---------|---------|
| ProductService | Products CRUD |
| FacilityService | Facilities hierarchy |
| StockService | Stock management |
| NotificationService | Notifications |
| ReceiptDocumentService | Receipt workflow |
| ShipmentDocumentService | Shipment workflow |
| IssueActService | Issue acts |
| InventoryActService | Inventory acts |
| LogisticsEventProducer | Kafka publish |
| LogisticsEventConsumer | Kafka consume |
| AuditService | Audit events |
| + 6 auth/security services | |

---

## Frontend Summary

### Components (11)

| Component | Purpose |
|-----------|---------|
| LoginPage | Auth |
| HomePage | Products list |
| AddProductPage | Add product |
| StatusPage | System status |
| AnalyticsPage | Analytics |
| FacilitySelector | Facility dropdown |
| documents/DocumentStatusBadge | Status badge |
| documents/DocumentList | Documents table |
| documents/DocumentDetail | Document view |
| documents/DocumentItemsTable | Items table |
| documents/DocumentActions | Action buttons |

### Views (22)

| Directory | Views |
|-----------|-------|
| views/dc/ | 7 (Dashboard, Receipts, Shipments) |
| views/wh/ | 8 (Dashboard, Receipts, Shipments, Stock, Inventory) |
| views/pp/ | 7 (Dashboard, Receipts, Issues, Stock) |

### Stores

| Store | State |
|-------|-------|
| facility.js | currentFacility, facilities, loading |

### Composables

| Composable | Methods |
|------------|---------|
| useDocument.js | fetchAll, create, approve, confirm, ship, deliver, complete |
| useFormValidation.js | validation rules |

### Routes (17 facility routes + 5 base)

| Base | Facility | Count |
|------|----------|-------|
| /login, /, /add, /status, /analytics | - | 5 |
| /dc/* | DC | 4 |
| /wh/* | WH | 6 |
| /pp/* | PP | 5 |

---

## State Machines

```
Receipt:   DRAFT → APPROVED → CONFIRMED → COMPLETED
Shipment:  DRAFT → APPROVED → SHIPPED → DELIVERED
IssueAct:  DRAFT → COMPLETED
Inventory: DRAFT → APPROVED → COMPLETED
```

## Kafka Auto-Documents

```
Shipment SHIPPED → logistics.shipments → auto Receipt (APPROVED)
Receipt CONFIRMED → logistics.receipts → Shipment DELIVERED
```

---

## Test Hierarchy

```
DC-C-001 (Центральный РЦ)
├── WH-C-001 (Склад Север)
│   ├── PP-C-001 (ПВЗ 1)
│   └── PP-C-002 (ПВЗ 2)
└── WH-C-002 (Склад Юг)
    ├── PP-C-003 (ПВЗ 3)
    └── PP-C-004 (ПВЗ 4)
```

---

## Окружения

| Env | API | Frontend |
|-----|-----|----------|
| Dev | 192.168.1.74:31080 | 192.168.1.74:31081 |
| Prod | 192.168.1.74:30080 | 192.168.1.74:30081 |
| Yandex | api.wh-lab.ru | wh-lab.ru |

---

## Следующая фаза: E2E Testing

### Что нужно

| Task | Description |
|------|-------------|
| Playwright setup | npm init playwright@latest |
| auth.spec.ts | Login/logout tests |
| facility.spec.ts | Facility selector tests |
| dc-flow.spec.ts | DC receipt/shipment workflow |
| wh-flow.spec.ts | WH workflow |
| pp-flow.spec.ts | PP issue workflow |
| full-flow.spec.ts | End-to-end flow |

### Deploy и Production Release

| Task | Description |
|------|-------------|
| Build & deploy dev | Test on warehouse-dev |
| MR develop → main | Code review |
| Deploy prod | Manual deploy |
| Smoke test | Verify all flows |

---

*Updated: 2025-12-12*
