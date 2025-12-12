# Фаза 4: E2E Testing & Release — Инструкция

## Обзор

Финальная фаза: Playwright тесты + production release.

```
Playwright Setup
    ↓
Auth Tests
    ↓
Facility Tests
    ↓
DC/WH/PP Flow Tests
    ↓
Full E2E Flow
    ↓
Deploy to Dev
    ↓
MR to Main
    ↓
Production Release
```

---

## Структура тестов

```
frontend/
├── tests/
│   ├── auth.spec.ts          # 4 tests
│   ├── facility.spec.ts      # 4 tests
│   ├── dc-flow.spec.ts       # 5 tests
│   ├── wh-flow.spec.ts       # 6 tests
│   ├── pp-flow.spec.ts       # 5 tests
│   └── full-flow.spec.ts     # 1 test (multi-step)
└── playwright.config.ts
```

**Total: 25+ tests**

---

# Блок 1: Playwright Setup

### Команды

```bash
cd frontend
npm init playwright@latest
# TypeScript: Yes
# Tests folder: tests
# GitHub Actions: No
# Install browsers: Yes
```

### Config

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  expect: { timeout: 5000 },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: 'http://192.168.1.74:31081',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
})
```

### Test Users

| User | Password | Facility | Type |
|------|----------|----------|------|
| admin | admin123 | - | ADMIN |
| dc_central_mgr | password123 | DC-C-001 | DC Manager |
| wh_north_op | password123 | WH-C-001 | WH Operator |
| wh_south_op | password123 | WH-C-002 | WH Operator |
| pp_1_op | password123 | PP-C-001 | PP Operator |
| pp_2_op | password123 | PP-C-002 | PP Operator |

### Checkpoint

```bash
npx playwright test --list
# Shows test files
```

**✅ STOP → Verify → Next**

---

# Блок 2: Auth Tests

### Создать

| File | Path |
|------|------|
| auth.spec.ts | frontend/tests/auth.spec.ts |

### Tests (4)

```typescript
import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('login with valid credentials', async ({ page }) => {
    await page.goto('/login')
    await page.fill('[data-testid="username"]', 'admin')
    await page.fill('[data-testid="password"]', 'admin123')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/')
  })

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login')
    await page.fill('[data-testid="username"]', 'admin')
    await page.fill('[data-testid="password"]', 'wrong')
    await page.click('[data-testid="login-button"]')
    await expect(page.locator('.error')).toBeVisible()
  })

  test('logout redirects to login', async ({ page }) => {
    // Login first
    await page.goto('/login')
    await page.fill('[data-testid="username"]', 'admin')
    await page.fill('[data-testid="password"]', 'admin123')
    await page.click('[data-testid="login-button"]')
    
    // Logout
    await page.click('[data-testid="logout-button"]')
    await expect(page).toHaveURL('/login')
  })

  test('protected route redirects to login', async ({ page }) => {
    await page.goto('/dc')
    await expect(page).toHaveURL(/\/login/)
  })
})
```

### Checkpoint

```bash
npx playwright test auth.spec.ts
# 4 passed
```

**✅ STOP → Verify → Next**

---

# Блок 3: Facility Tests

### Создать

| File | Path |
|------|------|
| facility.spec.ts | frontend/tests/facility.spec.ts |

### Tests (4)

```typescript
import { test, expect } from '@playwright/test'

test.describe('Facility Selector', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[data-testid="username"]', 'admin')
    await page.fill('[data-testid="password"]', 'admin123')
    await page.click('[data-testid="login-button"]')
    await page.waitForURL('/')
  })

  test('facility selector is visible after login', async ({ page }) => {
    await expect(page.locator('[data-testid="facility-selector"]')).toBeVisible()
  })

  test('can select facility from dropdown', async ({ page }) => {
    await page.click('[data-testid="facility-selector"]')
    await page.click('text=WH-C-001')
    await expect(page.locator('[data-testid="facility-selector"]')).toContainText('WH-C-001')
  })

  test('theme changes when facility type changes', async ({ page }) => {
    await page.click('[data-testid="facility-selector"]')
    await page.click('text=WH-C-001')
    await expect(page.locator('body')).toHaveClass(/facility-wh/)
  })

  test('user with facility auto-redirects', async ({ page }) => {
    await page.click('[data-testid="logout-button"]')
    await page.fill('[data-testid="username"]', 'wh_north_op')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/wh')
  })
})
```

### Checkpoint

```bash
npx playwright test facility.spec.ts
# 4 passed
```

**✅ STOP → Verify → Next**

---

# Блок 4: DC Flow Tests

### Создать

| File | Path |
|------|------|
| dc-flow.spec.ts | frontend/tests/dc-flow.spec.ts |

### Tests (5)

```typescript
import { test, expect } from '@playwright/test'

test.describe('DC Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[data-testid="username"]', 'dc_central_mgr')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await page.waitForURL('/dc')
  })

  test('dashboard loads with stats', async ({ page }) => {
    await expect(page.locator('[data-testid="receipts-count"]')).toBeVisible()
    await expect(page.locator('[data-testid="shipments-count"]')).toBeVisible()
  })

  test('can create receipt', async ({ page }) => {
    await page.click('text=Новый приход')
    await page.fill('[data-testid="supplier-name"]', 'Test Supplier')
    await page.click('[data-testid="add-item"]')
    // Add item logic
    await page.click('[data-testid="submit"]')
    await expect(page.locator('.success')).toBeVisible()
  })

  test('receipt workflow DRAFT → APPROVED → CONFIRMED', async ({ page }) => {
    await page.goto('/dc/receipts')
    await page.click('[data-testid="receipt-row"]:first-child')
    
    // Approve
    await page.click('[data-testid="approve-button"]')
    await expect(page.locator('[data-testid="status"]')).toContainText('APPROVED')
    
    // Confirm
    await page.click('[data-testid="confirm-button"]')
    await expect(page.locator('[data-testid="status"]')).toContainText('CONFIRMED')
  })

  test('can create shipment to WH', async ({ page }) => {
    await page.goto('/dc/shipments/create')
    await page.selectOption('[data-testid="destination"]', { label: 'WH-C-001' })
    await page.click('[data-testid="add-item"]')
    await page.click('[data-testid="submit"]')
    await expect(page.locator('.success')).toBeVisible()
  })

  test('shipment workflow DRAFT → APPROVED → SHIPPED', async ({ page }) => {
    await page.goto('/dc/shipments')
    await page.click('[data-testid="shipment-row"]:first-child')
    
    await page.click('[data-testid="approve-button"]')
    await expect(page.locator('[data-testid="status"]')).toContainText('APPROVED')
    
    await page.click('[data-testid="ship-button"]')
    await expect(page.locator('[data-testid="status"]')).toContainText('SHIPPED')
  })
})
```

### Checkpoint

```bash
npx playwright test dc-flow.spec.ts
# 5 passed
```

**✅ STOP → Verify → Next**

---

# Блок 5: WH Flow Tests

### Создать

| File | Path |
|------|------|
| wh-flow.spec.ts | frontend/tests/wh-flow.spec.ts |

### Tests (6)

```typescript
import { test, expect } from '@playwright/test'

test.describe('WH Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[data-testid="username"]', 'wh_north_op')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await page.waitForURL('/wh')
  })

  test('dashboard loads', async ({ page }) => {
    await expect(page.locator('[data-testid="incoming-receipts"]')).toBeVisible()
  })

  test('view incoming receipt from DC', async ({ page }) => {
    await page.goto('/wh/receipts')
    await expect(page.locator('[data-testid="receipt-row"]')).toBeVisible()
  })

  test('confirm receipt updates stock', async ({ page }) => {
    await page.goto('/wh/receipts')
    await page.click('[data-testid="receipt-row"]:first-child')
    await page.click('[data-testid="confirm-button"]')
    await expect(page.locator('[data-testid="status"]')).toContainText('CONFIRMED')
  })

  test('create shipment to PP', async ({ page }) => {
    await page.goto('/wh/shipments/create')
    await page.selectOption('[data-testid="destination"]', { label: 'PP-C-001' })
    await page.click('[data-testid="submit"]')
    await expect(page.locator('.success')).toBeVisible()
  })

  test('view stock list', async ({ page }) => {
    await page.goto('/wh/stock')
    await expect(page.locator('[data-testid="stock-table"]')).toBeVisible()
  })

  test('create inventory act', async ({ page }) => {
    await page.goto('/wh/inventory')
    await page.click('[data-testid="new-inventory"]')
    await page.click('[data-testid="submit"]')
    await expect(page.locator('.success')).toBeVisible()
  })
})
```

### Checkpoint

```bash
npx playwright test wh-flow.spec.ts
# 6 passed
```

**✅ STOP → Verify → Next**

---

# Блок 6: PP Flow Tests

### Создать

| File | Path |
|------|------|
| pp-flow.spec.ts | frontend/tests/pp-flow.spec.ts |

### Tests (5)

```typescript
import { test, expect } from '@playwright/test'

test.describe('PP Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[data-testid="username"]', 'pp_1_op')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await page.waitForURL('/pp')
  })

  test('dashboard loads', async ({ page }) => {
    await expect(page.locator('[data-testid="pending-receipts"]')).toBeVisible()
  })

  test('view incoming receipt from WH', async ({ page }) => {
    await page.goto('/pp/receipts')
    await expect(page.locator('[data-testid="receipt-row"]')).toBeVisible()
  })

  test('confirm receipt updates stock', async ({ page }) => {
    await page.goto('/pp/receipts')
    await page.click('[data-testid="receipt-row"]:first-child')
    await page.click('[data-testid="confirm-button"]')
    await expect(page.locator('[data-testid="status"]')).toContainText('CONFIRMED')
  })

  test('create issue act for customer', async ({ page }) => {
    await page.goto('/pp/issues/create')
    await page.fill('[data-testid="customer-name"]', 'Test Customer')
    await page.fill('[data-testid="customer-phone"]', '+7900000000')
    await page.click('[data-testid="submit"]')
    await expect(page.locator('.success')).toBeVisible()
  })

  test('complete issue deducts stock', async ({ page }) => {
    await page.goto('/pp/issues')
    await page.click('[data-testid="issue-row"]:first-child')
    await page.click('[data-testid="complete-button"]')
    await expect(page.locator('[data-testid="status"]')).toContainText('COMPLETED')
  })
})
```

### Checkpoint

```bash
npx playwright test pp-flow.spec.ts
# 5 passed
```

**✅ STOP → Verify → Next**

---

# Блок 7: Full E2E Flow

### Создать

| File | Path |
|------|------|
| full-flow.spec.ts | frontend/tests/full-flow.spec.ts |

### Test (1 multi-step)

```typescript
import { test, expect } from '@playwright/test'

test.describe('Full E2E Flow', () => {
  test('complete logistics flow DC → WH → PP → Customer', async ({ page }) => {
    // Step 1: DC creates receipt from supplier
    await page.goto('/login')
    await page.fill('[data-testid="username"]', 'dc_central_mgr')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    
    await page.goto('/dc/receipts/create')
    await page.fill('[data-testid="supplier-name"]', 'E2E Supplier')
    // Add items, submit
    await page.click('[data-testid="submit"]')
    
    // Approve and confirm receipt
    await page.click('[data-testid="approve-button"]')
    await page.click('[data-testid="confirm-button"]')
    
    // Step 2: DC creates shipment to WH
    await page.goto('/dc/shipments/create')
    await page.selectOption('[data-testid="destination"]', { label: 'WH-C-001' })
    await page.click('[data-testid="submit"]')
    await page.click('[data-testid="approve-button"]')
    await page.click('[data-testid="ship-button"]')
    
    // Step 3: WH confirms auto-created receipt
    await page.click('[data-testid="logout-button"]')
    await page.fill('[data-testid="username"]', 'wh_north_op')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    
    await page.goto('/wh/receipts')
    await page.click('[data-testid="receipt-row"]:first-child')
    await page.click('[data-testid="confirm-button"]')
    
    // Step 4: WH creates shipment to PP
    await page.goto('/wh/shipments/create')
    await page.selectOption('[data-testid="destination"]', { label: 'PP-C-001' })
    await page.click('[data-testid="submit"]')
    await page.click('[data-testid="approve-button"]')
    await page.click('[data-testid="ship-button"]')
    
    // Step 5: PP confirms receipt and issues to customer
    await page.click('[data-testid="logout-button"]')
    await page.fill('[data-testid="username"]', 'pp_1_op')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    
    await page.goto('/pp/receipts')
    await page.click('[data-testid="receipt-row"]:first-child')
    await page.click('[data-testid="confirm-button"]')
    
    // Step 6: PP issues to customer
    await page.goto('/pp/issues/create')
    await page.fill('[data-testid="customer-name"]', 'E2E Customer')
    await page.click('[data-testid="submit"]')
    await page.click('[data-testid="complete-button"]')
    
    await expect(page.locator('[data-testid="status"]')).toContainText('COMPLETED')
  })
})
```

### Checkpoint

```bash
npx playwright test full-flow.spec.ts
# 1 passed
```

**✅ STOP → Verify → Next**

---

# Блок 8: Run All Tests

```bash
cd frontend
npx playwright test

# Expected output:
# Running 25 tests using 1 worker
# ...
# 25 passed
```

### If all pass

```bash
git add .
git commit -m "Phase 4: Playwright E2E tests"
git push origin develop
```

**✅ STOP → Verify → Next**

---

# Блок 9: Deploy to Dev

### Build API

```bash
cd api
docker build --no-cache -t warehouse-api:latest .
sudo k3s ctr images rm docker.io/library/warehouse-api:latest 2>/dev/null || true
docker save warehouse-api:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/warehouse-api -n warehouse-dev
```

### Build Frontend

```bash
cd frontend
docker build --no-cache -t warehouse-frontend:latest .
sudo k3s ctr images rm docker.io/library/warehouse-frontend:latest 2>/dev/null || true
docker save warehouse-frontend:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/warehouse-frontend -n warehouse-dev
```

### Verify

```bash
curl http://192.168.1.74:31080/actuator/health
curl http://192.168.1.74:31081/
```

**✅ STOP → Verify → Next**

---

# Блок 10: Production Release

### MR develop → main

```bash
# In GitLab: Create MR from develop to main
# Code review
# Merge
```

### Deploy to Prod

```bash
kubectl rollout restart deployment/warehouse-api -n warehouse
kubectl rollout restart deployment/warehouse-frontend -n warehouse
```

### Smoke Test

```bash
curl http://192.168.1.74:30080/actuator/health
# Test login at http://192.168.1.74:30081
# Test facility workflow
```

### Yandex Cloud (optional)

```bash
ssh ubuntu@130.193.44.34
cd /opt/warehouse
sudo docker compose pull
sudo docker compose up -d
```

**✅ PHASE 4 COMPLETE**

---

## Summary

| Block | Tasks | Tests |
|-------|-------|-------|
| 1 | Playwright setup | - |
| 2 | Auth tests | 4 |
| 3 | Facility tests | 4 |
| 4 | DC flow tests | 5 |
| 5 | WH flow tests | 6 |
| 6 | PP flow tests | 5 |
| 7 | Full E2E flow | 1 |
| 8 | Run all tests | 25 |
| 9 | Deploy dev | - |
| 10 | Production release | - |

---

## Checklist

- [ ] Playwright installed
- [ ] 6 test files created
- [ ] 25+ tests passing
- [ ] Push to develop
- [ ] Deploy to warehouse-dev
- [ ] MR to main
- [ ] Deploy to warehouse (prod)
- [ ] Smoke test passed
- [ ] Yandex Cloud updated (optional)

---

*Updated: 2025-12-12*
