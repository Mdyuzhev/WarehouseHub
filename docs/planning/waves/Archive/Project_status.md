# Warehouse Project — Status (2025-12-11)

## Сводка

| Фаза | Название | Stories | Статус |
|------|----------|---------|--------|
| 0 | Инфраструктура | 3 | ✅ 3/3 |
| 1 | Модель данных | 3 | ✅ 3/3 |
| 2 | Документооборот | 4 | 🔄 0/4 ← CURRENT |
| 3 | Frontend | 3 | ⏳ 0/3 |
| 4 | Интеграция | 2 | ⏳ 0/2 |
| **Итого** | | **15** | **6/15 (40%)** |

---

## Фаза 1: Модель данных ✅ COMPLETE

### Flyway Migrations

| Version | File | Content |
|---------|------|---------|
| V2 | add_facilities.sql | Facilities table + FacilityType enum |
| V3 | add_notifications.sql | Notifications table |
| V4 | add_stock_table.sql | Stock table (product ↔ facility) |
| V5 | seed_facilities.sql | 7 test facilities (1 DC, 2 WH, 4 PP) |
| V6 | seed_facility_users.sql | 7 operators bound to facilities |
| V7 | seed_stock.sql | Stock records for WH/PP |

### Test Hierarchy

```
DC-C-001 (Центральный РЦ)
├── WH-C-001 (Склад Север)
│   ├── PP-C-001 (ПВЗ 1)
│   └── PP-C-002 (ПВЗ 2)
└── WH-C-002 (Склад Юг)
    ├── PP-C-003 (ПВЗ 3)
    └── PP-C-004 (ПВЗ 4)
```

### Current Models

| Model | Table | Fields |
|-------|-------|--------|
| Facility | facilities | id, type, code, name, address, parent_id |
| Stock | stock | id, product_id, facility_id, quantity, reserved |
| Product | products | id, name, quantity, price, created_by |
| User | users | id, username, password, role, facility_type, facility_id |
| Notification | notifications | id, channel, recipient, subject, body, status |

### Current Controllers

| Controller | Endpoints | Status |
|------------|-----------|--------|
| AuthController | /api/auth/* (4) | ✅ |
| ProductController | /api/products/* (5) | ✅ |
| FacilityController | /api/facilities/* (8) | ✅ |
| StockController | /api/stock/* (8) | ✅ |
| NotificationController | /api/notifications/* (3) | ✅ |

---

## Следующая: Фаза 2 — Документооборот

| Story | Описание | Entities |
|-------|----------|----------|
| WH-272 | Receipt Documents | ReceiptDocument, ReceiptItem |
| WH-273 | Shipment Documents | ShipmentDocument, ShipmentItem |
| WH-274 | Kafka Auto-Documents | Topics, Producers, Consumers |
| WH-275 | Issue & Inventory Acts | IssueAct, InventoryAct + Items |

---

*Updated: 2025-12-11*