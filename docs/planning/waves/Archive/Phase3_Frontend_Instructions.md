# Фаза 3: Frontend — Инструкция для агента

## Обзор

3 story + Playwright тесты. Выполняется автономно, блок за блоком.

```
WH-276: Navigation & Facility Selector
    ↓
WH-277: Document Components
    ↓
WH-278: Facility-Specific Screens
    ↓
Playwright E2E Tests
    ↓
Push to develop
```

---

## Общая информация

### Tech Stack Frontend

| Technology | Version |
|------------|---------|
| Vue.js | 3.4 |
| Vite | 5 |
| Vue Router | 4 |
| Pinia | 2 |
| Axios | для API |

### Текущие страницы

| Route | Component | Description |
|-------|-----------|-------------|
| /login | LoginView | Авторизация |
| /products | ProductsView | Список товаров |
| /add | AddProductView | Добавление товара |
| /status | StatusView | Статус системы (ADMIN) |
| /analytics | AnalyticsView | Аналитика |

### API Endpoints (Backend готов)

| Group | Base Path | Endpoints |
|-------|-----------|-----------|
| Auth | /api/auth | login, logout, me, register |
| Facilities | /api/facilities | CRUD, /tree |
| Stock | /api/stock | by facility, by product, adjust, reserve |
| Receipts | /api/receipts | CRUD, approve, confirm, complete |
| Shipments | /api/shipments | CRUD, approve, ship, deliver, cancel |
| IssueActs | /api/issue-acts | CRUD, complete |
| InventoryActs | /api/inventory-acts | CRUD, approve, complete |

### Структура проекта frontend

```
src/
├── assets/
├── components/
├── composables/
├── router/
├── stores/
├── views/
└── App.vue
```

### Образцы в проекте

| Паттерн | Файл |
|---------|------|
| View | views/ProductsView.vue |
| Component | components/*.vue |
| Store | stores/auth.js |
| Router | router/index.js |
| API call | Axios в компонентах |

---

# WH-276: Navigation & Facility Selector

## Цель
Добавить выбор facility в header, роутинг по типам объектов, цветовые схемы.

---

## Блок 1: Pinia Store — currentFacility (WH-342)

### Файл создать

| Файл | Путь |
|------|------|
| facility.js | src/stores/facility.js |

### Store state

| Field | Type | Description |
|-------|------|-------------|
| currentFacility | Object | {id, code, name, type} |
| facilities | Array | Все доступные facilities |
| loading | Boolean | Загрузка |

### Store actions

| Action | Description |
|--------|-------------|
| fetchFacilities() | GET /api/facilities |
| setCurrentFacility(facility) | Установить текущий объект |
| clearFacility() | Сбросить выбор |

### Store getters

| Getter | Description |
|--------|-------------|
| facilityType | DC / WH / PP |
| facilityCode | Код объекта |
| hasFacility | Boolean — выбран ли объект |

**Образец:** stores/auth.js

### Checkpoint Блок 1

```bash
# Проверить что store импортируется без ошибок
npm run dev
# Console: no errors
```

**✅ STOP → Verify → Next**

---

## Блок 2: FacilitySelector Component (WH-338)

### Файл создать

| Файл | Путь |
|------|------|
| FacilitySelector.vue | src/components/FacilitySelector.vue |

### Props

| Prop | Type | Description |
|------|------|-------------|
| - | - | Использует store напрямую |

### Функционал

- Dropdown с группировкой по type (DC, WH, PP)
- Показывает текущий выбранный facility
- При смене — обновляет store
- Иконки по типу объекта

### UI структура

```
[▼ DC-C-001 — Центральный РЦ]
    ├── DC
    │   └── DC-C-001 — Центральный РЦ
    ├── WH
    │   ├── WH-C-001 — Склад Север
    │   └── WH-C-002 — Склад Юг
    └── PP
        ├── PP-C-001 — ПВЗ 1
        └── ...
```

**Образец:** Любой dropdown компонент в проекте

### Checkpoint Блок 2

```bash
# Компонент рендерится, dropdown открывается
npm run dev
# Визуально проверить в браузере
```

**✅ STOP → Verify → Next**

---

## Блок 3: Header Integration (WH-344)

### Файл изменить

| Файл | Изменение |
|------|-----------|
| App.vue или Header.vue | Добавить FacilitySelector |

### Изменения

- Импортировать FacilitySelector
- Добавить в header справа от навигации
- Показывать только для авторизованных пользователей
- При logout — сбрасывать facility

### Checkpoint Блок 3

```bash
# Header показывает selector после login
npm run dev
# Login → видим FacilitySelector
```

**✅ STOP → Verify → Next**

---

## Блок 4: Facility-based Routing (WH-339)

### Файл изменить

| Файл | Изменение |
|------|-----------|
| router/index.js | Добавить facility routes |

### Новые routes

| Route | Component | Description |
|-------|-----------|-------------|
| /dc | DCDashboard | Dashboard для DC |
| /dc/receipts | ReceiptsList | Приходные накладные DC |
| /dc/shipments | ShipmentsList | Расходные DC → WH |
| /wh | WHDashboard | Dashboard для WH |
| /wh/receipts | ReceiptsList | Приходные WH (от DC) |
| /wh/shipments | ShipmentsList | Расходные WH → PP |
| /wh/stock | StockList | Остатки на складе |
| /wh/inventory | InventoryList | Инвентаризация |
| /pp | PPDashboard | Dashboard для PP |
| /pp/receipts | ReceiptsList | Приходные PP (от WH) |
| /pp/issues | IssuesList | Выдача клиентам |
| /pp/stock | StockList | Остатки в ПВЗ |

### Route guards

- Проверять что выбран facility нужного типа
- Redirect на выбор facility если не выбран

**Образец:** router/index.js (существующие guards)

### Checkpoint Блок 4

```bash
# Routes работают, guards срабатывают
npm run dev
# Перейти на /wh без выбора facility → redirect
```

**✅ STOP → Verify → Next**

---

## Блок 5: Color Schemes by Facility Type (WH-341)

### Файлы создать/изменить

| Файл | Путь |
|------|------|
| facility-themes.css | src/assets/facility-themes.css |

### Цветовые схемы

| Type | Primary | Background | Accent |
|------|---------|------------|--------|
| DC | #1E40AF (blue) | #EFF6FF | #3B82F6 |
| WH | #166534 (green) | #F0FDF4 | #22C55E |
| PP | #9333EA (purple) | #FAF5FF | #A855F7 |

### Применение

- CSS класс на body или main container: `.facility-dc`, `.facility-wh`, `.facility-pp`
- Менять при смене facility в store
- Header, sidebar, buttons используют CSS variables

### Checkpoint Блок 5

```bash
# Цвета меняются при смене facility type
npm run dev
# Выбрать DC → синяя тема
# Выбрать WH → зелёная тема
# Выбрать PP → фиолетовая тема
```

**✅ STOP → Verify → Next**

---

## Блок 6: Auto-redirect by User Role (WH-343)

### Файл изменить

| Файл | Изменение |
|------|-----------|
| router/index.js | После login — redirect по facility |

### Логика

```
После успешного login:
  1. Получить user из /api/auth/me
  2. Если user.facilityId:
     - Установить facility в store
     - Redirect на dashboard по facilityType
  3. Если нет facilityId:
     - Показать FacilitySelector
     - После выбора → redirect
```

### Checkpoint Блок 6

```bash
# Login как wh_north_op → redirect на /wh
# Login как admin → остаётся на выбор facility
```

**✅ STOP → Verify → WH-276 DONE**

---

# WH-277: Document Components

## Цель
Универсальные компоненты для работы с документами.

---

## Блок 1: DocumentStatusBadge (WH-346)

### Файл создать

| Файл | Путь |
|------|------|
| DocumentStatusBadge.vue | src/components/documents/DocumentStatusBadge.vue |

### Props

| Prop | Type | Values |
|------|------|--------|
| status | String | DRAFT, APPROVED, CONFIRMED, COMPLETED, SHIPPED, DELIVERED |
| type | String | receipt, shipment, issue, inventory |

### Цвета по статусу

| Status | Color | Icon |
|--------|-------|------|
| DRAFT | gray | ✏️ |
| APPROVED | blue | ✓ |
| CONFIRMED | green | ✓✓ |
| COMPLETED | green-dark | ✓✓✓ |
| SHIPPED | orange | 🚚 |
| DELIVERED | green | 📦 |

### Checkpoint Блок 1

```bash
# Badge рендерится с правильными цветами
```

**✅ STOP → Verify → Next**

---

## Блок 2: DocumentList Component (WH-345)

### Файл создать

| Файл | Путь |
|------|------|
| DocumentList.vue | src/components/documents/DocumentList.vue |

### Props

| Prop | Type | Description |
|------|------|-------------|
| documents | Array | Список документов |
| type | String | receipt, shipment, issue, inventory |
| loading | Boolean | Загрузка |

### Columns

| Column | Description |
|--------|-------------|
| № документа | documentNumber |
| Дата | createdAt |
| Статус | DocumentStatusBadge |
| Позиций | items.length |
| Сумма qty | totalQuantity |
| Действия | View, Edit (if DRAFT), Actions |

### Events

| Event | Payload |
|-------|---------|
| @view | document.id |
| @edit | document.id |
| @action | {id, action} |

### Checkpoint Блок 2

```bash
# Таблица рендерится, сортировка работает
```

**✅ STOP → Verify → Next**

---

## Блок 3: DocumentDetail Component (WH-347)

### Файл создать

| Файл | Путь |
|------|------|
| DocumentDetail.vue | src/components/documents/DocumentDetail.vue |

### Props

| Prop | Type | Description |
|------|------|-------------|
| document | Object | Документ с items |
| type | String | receipt, shipment, issue, inventory |

### Sections

- Header: номер, дата, статус, facility
- Info: supplier/destination, notes
- Items: DocumentItemsTable
- History: timeline изменений статуса
- Actions: DocumentActions

### Checkpoint Блок 3

```bash
# Detail view отображает все секции
```

**✅ STOP → Verify → Next**

---

## Блок 4: DocumentItemsTable (WH-348)

### Файл создать

| Файл | Путь |
|------|------|
| DocumentItemsTable.vue | src/components/documents/DocumentItemsTable.vue |

### Props

| Prop | Type | Description |
|------|------|-------------|
| items | Array | Позиции документа |
| type | String | receipt, shipment, issue, inventory |
| editable | Boolean | Можно редактировать qty |

### Columns по типу

**Receipt:**
| Column | Field |
|--------|-------|
| Товар | productName |
| Ожидаемое | expectedQuantity |
| Фактическое | actualQuantity (editable) |
| Разница | computed |

**Shipment:**
| Column | Field |
|--------|-------|
| Товар | productName |
| Количество | quantity |

**Inventory:**
| Column | Field |
|--------|-------|
| Товар | productName |
| По системе | expectedQuantity |
| Фактически | actualQuantity (editable) |
| Разница | difference |

### Checkpoint Блок 4

```bash
# Таблица показывает items, editable работает
```

**✅ STOP → Verify → Next**

---

## Блок 5: DocumentActions (WH-349)

### Файл создать

| Файл | Путь |
|------|------|
| DocumentActions.vue | src/components/documents/DocumentActions.vue |

### Props

| Prop | Type | Description |
|------|------|-------------|
| document | Object | Документ |
| type | String | receipt, shipment, issue, inventory |

### Actions по типу и статусу

**Receipt:**
| Status | Actions |
|--------|---------|
| DRAFT | Edit, Delete, Approve |
| APPROVED | Confirm |
| CONFIRMED | Complete |
| COMPLETED | - |

**Shipment:**
| Status | Actions |
|--------|---------|
| DRAFT | Edit, Delete, Approve |
| APPROVED | Ship, Cancel |
| SHIPPED | Deliver |
| DELIVERED | - |

**IssueAct:**
| Status | Actions |
|--------|---------|
| DRAFT | Edit, Delete, Complete |
| COMPLETED | - |

**InventoryAct:**
| Status | Actions |
|--------|---------|
| DRAFT | Edit, Delete, Approve |
| APPROVED | Complete |
| COMPLETED | - |

### Events

| Event | Payload |
|-------|---------|
| @action | {action, documentId} |

### Checkpoint Блок 5

```bash
# Кнопки показываются по статусу, emit работает
```

**✅ STOP → Verify → Next**

---

## Блок 6: useDocument Composable (WH-350)

### Файл создать

| Файл | Путь |
|------|------|
| useDocument.js | src/composables/useDocument.js |

### API

```javascript
const {
  documents,
  document,
  loading,
  error,
  fetchAll,
  fetchById,
  create,
  approve,
  confirm,
  complete,
  ship,
  deliver,
  cancel,
  remove
} = useDocument('receipts') // or 'shipments', 'issue-acts', 'inventory-acts'
```

### Методы

| Method | HTTP | Endpoint |
|--------|------|----------|
| fetchAll(facilityId) | GET | /api/{type}/facility/{id} |
| fetchById(id) | GET | /api/{type}/{id} |
| create(data) | POST | /api/{type} |
| approve(id) | POST | /api/{type}/{id}/approve |
| confirm(id, data) | POST | /api/{type}/{id}/confirm |
| complete(id) | POST | /api/{type}/{id}/complete |
| ship(id) | POST | /api/{type}/{id}/ship |
| deliver(id) | POST | /api/{type}/{id}/deliver |
| cancel(id) | POST | /api/{type}/{id}/cancel |
| remove(id) | DELETE | /api/{type}/{id} |

**Образец:** существующие API calls в проекте

### Checkpoint Блок 6

```bash
# Composable работает, API вызовы проходят
```

**✅ STOP → Verify → Next**

---

## Блок 7: Form Validation (WH-351)

### Файл создать

| Файл | Путь |
|------|------|
| useFormValidation.js | src/composables/useFormValidation.js |

### Rules

| Field | Validation |
|-------|------------|
| facilityId | required |
| items | required, min 1 |
| items[].productId | required |
| items[].quantity | required, > 0 |
| supplierName | optional, max 255 |
| notes | optional |

### API

```javascript
const { validate, errors, isValid } = useFormValidation(rules)
```

### Checkpoint Блок 7

```bash
# Валидация срабатывает, ошибки показываются
```

**✅ STOP → Verify → WH-277 DONE**

---

# WH-278: Facility-Specific Screens

## Цель
Экраны для каждого типа facility.

---

## Блок 1: DC Dashboard (WH-354)

### Файл создать

| Файл | Путь |
|------|------|
| DCDashboard.vue | src/views/dc/DCDashboard.vue |

### Sections

| Section | Data |
|---------|------|
| Stats cards | Total receipts, shipments today |
| Recent receipts | Last 5 |
| Pending shipments | DRAFT + APPROVED |
| Quick actions | New Receipt, New Shipment |

### API calls

- GET /api/receipts/facility/{facilityId}
- GET /api/shipments/facility/{facilityId}

### Checkpoint Блок 1

```bash
# DC Dashboard загружается, показывает данные
npm run dev → /dc
```

**✅ STOP → Verify → Next**

---

## Блок 2: DC Receipts (WH-352)

### Файлы создать

| Файл | Путь |
|------|------|
| DCReceiptsList.vue | src/views/dc/DCReceiptsList.vue |
| DCReceiptCreate.vue | src/views/dc/DCReceiptCreate.vue |
| DCReceiptDetail.vue | src/views/dc/DCReceiptDetail.vue |

### DCReceiptsList

- Использует DocumentList
- Фильтры: по статусу, по дате
- Кнопка "Создать"

### DCReceiptCreate

- Форма: supplierName, notes
- Добавление items (product + expectedQuantity)
- Валидация
- Submit → POST /api/receipts

### DCReceiptDetail

- Использует DocumentDetail
- Actions: approve, confirm, complete
- При confirm — ввод actualQuantity

### Checkpoint Блок 2

```bash
# CRUD receipts работает
# Создать receipt → approve → confirm → complete
```

**✅ STOP → Verify → Next**

---

## Блок 3: DC Shipments (WH-353)

### Файлы создать

| Файл | Путь |
|------|------|
| DCShipmentsList.vue | src/views/dc/DCShipmentsList.vue |
| DCShipmentCreate.vue | src/views/dc/DCShipmentCreate.vue |
| DCShipmentDetail.vue | src/views/dc/DCShipmentDetail.vue |

### DCShipmentCreate

- Выбор destination facility (только WH, children of current DC)
- Добавление items (product + quantity)
- Показ available stock

### DCShipmentDetail

- Actions: approve (reserve), ship, deliver
- Показывает linked receipt (если auto-created)

### Checkpoint Блок 3

```bash
# Shipment DC → WH работает
# Ship → проверить auto-created receipt на WH
```

**✅ STOP → Verify → Next**

---

## Блок 4: WH Dashboard + Screens (WH-355, WH-356, WH-357)

### Файлы создать

| Файл | Path |
|------|------|
| WHDashboard.vue | src/views/wh/WHDashboard.vue |
| WHReceiptsList.vue | src/views/wh/WHReceiptsList.vue |
| WHReceiptDetail.vue | src/views/wh/WHReceiptDetail.vue |
| WHShipmentsList.vue | src/views/wh/WHShipmentsList.vue |
| WHShipmentCreate.vue | src/views/wh/WHShipmentCreate.vue |
| WHShipmentDetail.vue | src/views/wh/WHShipmentDetail.vue |
| WHStockList.vue | src/views/wh/WHStockList.vue |
| WHInventory.vue | src/views/wh/WHInventory.vue |

### WHDashboard sections

- Stats: receipts pending, shipments pending, low stock
- Incoming (receipts from DC)
- Outgoing (shipments to PP)
- Stock alerts

### WHReceiptsList

- Показывает receipts (включая auto-created from shipments)
- Actions: confirm (ввести actual qty)

### WHShipmentCreate

- Destination: PP facilities (children of current WH)
- Stock validation перед добавлением

### WHStockList

- Таблица: product, quantity, reserved, available
- Фильтр: low stock
- Actions: adjust stock

### WHInventory

- Создание InventoryAct
- Сравнение system vs actual
- Complete → stock correction

### Checkpoint Блок 4

```bash
# WH screens работают
# Receipt from DC → confirm
# Shipment to PP → ship
# Inventory → complete
```

**✅ STOP → Verify → Next**

---

## Блок 5: PP Dashboard + Screens (WH-358, WH-359)

### Файлы создать

| Файл | Path |
|------|------|
| PPDashboard.vue | src/views/pp/PPDashboard.vue |
| PPReceiptsList.vue | src/views/pp/PPReceiptsList.vue |
| PPReceiptDetail.vue | src/views/pp/PPReceiptDetail.vue |
| PPIssuesList.vue | src/views/pp/PPIssuesList.vue |
| PPIssueCreate.vue | src/views/pp/PPIssueCreate.vue |
| PPIssueDetail.vue | src/views/pp/PPIssueDetail.vue |
| PPStockList.vue | src/views/pp/PPStockList.vue |

### PPDashboard sections

- Stats: pending receipts, today's issues
- Stock status
- Quick issue button

### PPIssueCreate

- Customer info: name, phone
- Items from available stock
- Complete → instant stock deduction

### PPStockList

- Compact view for PP
- Low stock alerts

### Checkpoint Блок 5

```bash
# PP screens работают
# Receipt from WH → confirm
# Issue to customer → complete → stock deducted
```

**✅ STOP → Verify → Next**

---

## Блок 6: Products → Stock Adaptation (WH-360)

### Файлы изменить

| Файл | Изменение |
|------|-----------|
| ProductsView.vue | Показывать stock по текущему facility |

### Изменения

- Если выбран facility:
  - Показывать stock.quantity вместо product.quantity
  - Добавить колонки: reserved, available
  - Quick actions: adjust stock
- Если не выбран:
  - Показывать суммарный stock по всем facilities
  - Или total из product.quantity

### Checkpoint Блок 6

```bash
# Products view адаптирован под facility
# Stock отображается корректно
```

**✅ STOP → Verify → WH-278 DONE**

---

# Playwright E2E Tests

## Цель
Покрытие всех страниц автотестами.

---

## Блок 1: Setup Playwright

### Установка

```bash
cd warehouse-frontend
npm init playwright@latest
# Выбрать: TypeScript, tests folder, GitHub Actions: No
```

### Конфигурация

| Файл | Настройка |
|------|-----------|
| playwright.config.ts | baseURL: http://192.168.1.74:31081 |

### Test credentials

| User | Password | Facility |
|------|----------|----------|
| dc_manager | password123 | DC-C-001 |
| wh_north_op | password123 | WH-C-001 |
| pp_1_op | password123 | PP-C-001 |
| admin | admin123 | - |

### Checkpoint Блок 1

```bash
npx playwright test --list
# Shows test files
```

**✅ STOP → Verify → Next**

---

## Блок 2: Auth Tests

### Файл создать

| Файл | Путь |
|------|------|
| auth.spec.ts | tests/auth.spec.ts |

### Tests

| Test | Description |
|------|-------------|
| login with valid credentials | Login → redirect to dashboard |
| login with invalid credentials | Error message shown |
| logout | Redirect to login, token cleared |
| protected route redirect | /wh without auth → /login |

### Checkpoint Блок 2

```bash
npx playwright test auth.spec.ts
# 4 tests passed
```

**✅ STOP → Verify → Next**

---

## Блок 3: Facility Selector Tests

### Файл создать

| Файл | Путь |
|------|------|
| facility.spec.ts | tests/facility.spec.ts |

### Tests

| Test | Description |
|------|-------------|
| facility selector visible after login | Selector in header |
| change facility updates theme | Color scheme changes |
| facility persists on page reload | Store persisted |
| auto-redirect by user facility | wh_north_op → /wh |

### Checkpoint Блок 3

```bash
npx playwright test facility.spec.ts
# 4 tests passed
```

**✅ STOP → Verify → Next**

---

## Блок 4: DC Flow Tests

### Файл создать

| Файл | Путь |
|------|------|
| dc-flow.spec.ts | tests/dc-flow.spec.ts |

### Tests

| Test | Description |
|------|-------------|
| DC dashboard loads | Stats, recent docs visible |
| create receipt | Form → submit → appears in list |
| receipt workflow | DRAFT → APPROVED → CONFIRMED → COMPLETED |
| create shipment to WH | Select destination, add items |
| shipment workflow | DRAFT → APPROVED → SHIPPED |

### Checkpoint Блок 4

```bash
npx playwright test dc-flow.spec.ts
# 5 tests passed
```

**✅ STOP → Verify → Next**

---

## Блок 5: WH Flow Tests

### Файл создать

| Файл | Путь |
|------|------|
| wh-flow.spec.ts | tests/wh-flow.spec.ts |

### Tests

| Test | Description |
|------|-------------|
| WH dashboard loads | Stats visible |
| view incoming receipt | Auto-created from DC shipment |
| confirm receipt | Enter actual qty → stock updated |
| create shipment to PP | Select PP, add items |
| view stock | Stock table with quantities |
| create inventory act | System qty vs actual |
| complete inventory | Stock corrected |

### Checkpoint Блок 5

```bash
npx playwright test wh-flow.spec.ts
# 7 tests passed
```

**✅ STOP → Verify → Next**

---

## Блок 6: PP Flow Tests

### Файл создать

| Файл | Путь |
|------|------|
| pp-flow.spec.ts | tests/pp-flow.spec.ts |

### Tests

| Test | Description |
|------|-------------|
| PP dashboard loads | Stats visible |
| view incoming receipt | From WH shipment |
| confirm receipt | Stock updated |
| create issue act | Customer info, items |
| complete issue | Stock deducted |
| view stock | Available for issue |

### Checkpoint Блок 6

```bash
npx playwright test pp-flow.spec.ts
# 6 tests passed
```

**✅ STOP → Verify → Next**

---

## Блок 7: Full E2E Flow Test

### Файл создать

| Файл | Путь |
|------|------|
| full-flow.spec.ts | tests/full-flow.spec.ts |

### Test: End-to-End Logistics Flow

```
1. Login as dc_manager
2. Create receipt (supplier → DC)
3. Confirm receipt → stock on DC
4. Create shipment DC → WH-C-001
5. Approve + Ship

6. Login as wh_north_op
7. See auto-created receipt
8. Confirm receipt → stock on WH
9. Create shipment WH → PP-C-001
10. Approve + Ship

11. Login as pp_1_op
12. See auto-created receipt
13. Confirm receipt → stock on PP
14. Create issue act (customer)
15. Complete issue → stock deducted

16. Verify: stock flow correct through all facilities
```

### Checkpoint Блок 7

```bash
npx playwright test full-flow.spec.ts
# 1 test passed (multi-step)
```

**✅ STOP → Verify → Next**

---

## Блок 8: Run All Tests + Push

### Команды

```bash
# Run all tests
npx playwright test

# Expected: 27+ tests passed

# If all pass:
git add .
git commit -m "WH-276,277,278: Phase 3 Frontend + Playwright tests"
git push origin develop
```

### CI Integration (optional)

Добавить в .gitlab-ci.yml:

```yaml
test-frontend:
  stage: test
  script:
    - cd warehouse-frontend
    - npm ci
    - npx playwright install --with-deps
    - npx playwright test
  only:
    - develop
    - main
```

### Checkpoint Блок 8

```bash
# All tests pass
npx playwright test
# 27+ passed

# Push successful
git push origin develop
```

**✅ PHASE 3 COMPLETE**

---

# Порядок выполнения (Summary)

```
WH-276 Navigation & Facility Selector
├── Блок 1: Pinia store facility.js
├── Блок 2: FacilitySelector component
├── Блок 3: Header integration
├── Блок 4: Facility-based routing
├── Блок 5: Color schemes
└── Блок 6: Auto-redirect by role

WH-277 Document Components
├── Блок 1: DocumentStatusBadge
├── Блок 2: DocumentList
├── Блок 3: DocumentDetail
├── Блок 4: DocumentItemsTable
├── Блок 5: DocumentActions
├── Блок 6: useDocument composable
└── Блок 7: Form validation

WH-278 Facility-Specific Screens
├── Блок 1: DC Dashboard
├── Блок 2: DC Receipts (list, create, detail)
├── Блок 3: DC Shipments (list, create, detail)
├── Блок 4: WH screens (all)
├── Блок 5: PP screens (all)
└── Блок 6: Products → Stock adaptation

Playwright E2E Tests
├── Блок 1: Setup
├── Блок 2: Auth tests
├── Блок 3: Facility tests
├── Блок 4: DC flow tests
├── Блок 5: WH flow tests
├── Блок 6: PP flow tests
├── Блок 7: Full E2E flow
└── Блок 8: Run all + Push develop
```

---

# Критерии готовности Фазы 3

- [ ] FacilitySelector работает в header
- [ ] Цветовые схемы по типу facility
- [ ] DC/WH/PP dashboards загружаются
- [ ] Receipt CRUD + workflow на всех уровнях
- [ ] Shipment CRUD + workflow (DC→WH, WH→PP)
- [ ] Issue acts на PP
- [ ] Inventory acts на WH
- [ ] Stock отображается корректно
- [ ] Playwright tests: 27+ passed
- [ ] Push to develop successful

---

# Важные замечания

1. **API URL:** Использовать `window.__API_URL__` (см. project-context.md)
2. **Auth token:** Хранится в localStorage, добавлять в headers
3. **Facility store:** Persist в localStorage
4. **Dev server:** http://192.168.1.74:31081
5. **API dev:** http://192.168.1.74:31080

---

*Next Action: WH-276 Блок 1 — Pinia store facility.js*
