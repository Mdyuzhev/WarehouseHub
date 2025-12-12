# Фаза 2: Документооборот - Задачи для GitHub Issues

## ✅ ЗАВЕРШЕННЫЕ ЗАДАЧИ (нужно создать и закрыть)

### WH-272: Receipt Documents (Приходные накладные)
**Status:** CLOSED
**Labels:** enhancement, Phase 2, документооборот
**Description:**
Реализация приходных накладных для учета поступления товаров на склады/ПВЗ.

**Acceptance Criteria:**
- [x] V8 migration: receipt_documents, receipt_items tables
- [x] Entities: ReceiptDocument, ReceiptItem, ReceiptStatus (DRAFT/APPROVED/CONFIRMED/COMPLETED)
- [x] Repository + DTOs (ReceiptDocumentDTO, ReceiptItemDTO, ReceiptCreateRequest, ReceiptConfirmRequest)
- [x] Service: create, approve, confirm (stock update), complete, delete
- [x] Controller: 7 REST endpoints
- [x] Unit tests: 18/18 passed (Service: 11, Controller: 7)

**Commits:**
- Multiple commits in develop branch

---

### WH-273: Shipment Documents (Расходные накладные)
**Status:** CLOSED
**Labels:** enhancement, Phase 2, документооборот
**Description:**
Реализация расходных накладных для учета отгрузки товаров со складов.

**Acceptance Criteria:**
- [x] V9 migration: shipment_documents, shipment_items tables
- [x] Entities: ShipmentDocument, ShipmentItem, ShipmentStatus (DRAFT/APPROVED/SHIPPED/DELIVERED)
- [x] Repository + DTOs
- [x] Service: create, approve (reserve stock), ship (deduct stock), deliver, cancel
- [x] Controller: 7 REST endpoints
- [x] Unit tests: 16/16 passed (Service: 9, Controller: 7)

**Commits:**
- 361aff0 WH-273.2: Add Shipment Documents Service + Controller + DTOs
- 857ca8f WH-273.3: Add Shipment Documents Unit Tests

---

### WH-274: Kafka Auto-Documents (Автоматическое создание документов)
**Status:** CLOSED
**Labels:** enhancement, Phase 2, kafka, integration
**Description:**
Kafka integration для автоматического создания Receipt при отгрузке Shipment.

**Acceptance Criteria:**
- [x] Kafka topics: logistics.shipments, logistics.receipts
- [x] V10 migration: source_shipment_id link в receipt_documents
- [x] ShipmentEvent DTO + LogisticsEventProducer
- [x] LogisticsEventConsumer: auto-create Receipt при shipment.SHIPPED
- [x] Receipt.confirm() → Shipment.DELIVERED через Kafka
- [x] KafkaConfig: ConsumerFactory + ListenerContainerFactory

**Commits:**
- a67c31d WH-274.1: Add Kafka topics + Receipt-Shipment link
- 1c2cecf WH-274.2: Add ShipmentEvent + LogisticsEventProducer
- b9a4cee WH-274.3: Add LogisticsEventConsumer for auto-receipts
- 8c82684 WH-274.4: Link Receipt confirm → Shipment delivered

**Note:** Integration tests пропущены (требуют полное Kafka окружение)

---

### WH-275: Issue & Inventory Acts (Акты выдачи и инвентаризации)
**Status:** CLOSED
**Labels:** enhancement, Phase 2, документооборот
**Description:**
Реализация актов выдачи товара (для ПВЗ) и актов инвентаризации (корректировка остатков).

**Acceptance Criteria:**

**IssueAct (Акты выдачи):**
- [x] V11 migration: issue_acts, issue_act_items (только PP)
- [x] Entities: IssueAct, IssueActItem, IssueStatus (DRAFT/COMPLETED)
- [x] Repository + DTOs
- [x] Service: create, complete (instant stock deduction), delete
- [x] Controller: 5 REST endpoints

**InventoryAct (Акты инвентаризации):**
- [x] V12 migration: inventory_acts, inventory_act_items
- [x] Entities: InventoryAct, InventoryActItem, InventoryStatus (DRAFT/COMPLETED)
- [x] Repository + DTOs
- [x] Service: create, complete (stock correction based on difference), delete
- [x] Controller: 5 REST endpoints

**Commits:**
- 146b3c1 WH-275.1: Add IssueAct entities + migration
- b165456 WH-275.2: Add IssueAct Service + Controller + DTOs
- 2eeaa18 WH-275.3: Add InventoryAct entities + migration
- a0a8f7f WH-275.4: Add InventoryAct Service + Controller + DTOs

---

## 📊 СТАТИСТИКА ФАЗЫ 2

**Реализовано блоков:** 19/20 (95%)
**Коммитов:** 13
**Миграций:** V8-V12 (5 migrations)
**REST Endpoints:** 24
**Тесты:** 34 unit/integration tests
**Строк кода:** ~3500+

**Branch:** develop
**Latest commit:** a0a8f7f

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

1. ✅ Push to develop - DONE
2. ⏭️ Deploy to warehouse-dev (K3s)
3. ⏭️ Manual testing в dev environment
4. ⏭️ Create GitHub issues (требуется gh CLI или web UI)
5. ⏭️ Merge to main после тестирования

---

## 📝 КОМАНДЫ ДЛЯ СОЗДАНИЯ ЗАДАЧ В GITHUB

```bash
# WH-272: Receipt Documents
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "WH-272: Receipt Documents (Приходные накладные)" \
  --label "enhancement,Phase 2,документооборот" \
  --body "$(cat <<EOF
Реализация приходных накладных для учета поступления товаров.

✅ Реализовано:
- V8 migration
- Entities + Repository + DTOs
- Service + Controller (7 endpoints)
- Unit tests: 18/18 passed

Commits: develop branch
EOF
)"
gh issue close <number> --repo Mdyuzhev/WaregouseHub

# WH-273: Shipment Documents
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "WH-273: Shipment Documents (Расходные накладные)" \
  --label "enhancement,Phase 2,документооборот" \
  --body "$(cat <<EOF
Реализация расходных накладных для учета отгрузки товаров.

✅ Реализовано:
- V9 migration
- Entities + Repository + DTOs
- Service + Controller (7 endpoints)
- Unit tests: 16/16 passed

Commits: 361aff0, 857ca8f
EOF
)"
gh issue close <number> --repo Mdyuzhev/WaregouseHub

# WH-274: Kafka Auto-Documents
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "WH-274: Kafka Auto-Documents" \
  --label "enhancement,Phase 2,kafka,integration" \
  --body "$(cat <<EOF
Kafka integration для автоматического создания документов.

✅ Реализовано:
- Kafka topics + Consumer/Producer
- Auto-create Receipt при shipment
- Update Shipment при receipt.confirm
- V10 migration для связей

Commits: a67c31d, 1c2cecf, b9a4cee, 8c82684
EOF
)"
gh issue close <number> --repo Mdyuzhev/WaregouseHub

# WH-275: Issue & Inventory Acts
gh issue create --repo Mdyuzhev/WaregouseHub \
  --title "WH-275: Issue & Inventory Acts (Акты выдачи и инвентаризации)" \
  --label "enhancement,Phase 2,документооборот" \
  --body "$(cat <<EOF
Реализация актов выдачи (ПВЗ) и инвентаризации.

✅ Реализовано:
- IssueAct: V11 migration + Service + Controller
- InventoryAct: V12 migration + Service + Controller
- Instant stock deduction & correction

Commits: 146b3c1, b165456, 2eeaa18, a0a8f7f
EOF
)"
gh issue close <number> --repo Mdyuzhev/WaregouseHub
```
