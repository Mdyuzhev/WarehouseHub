# Playwright E2E Tests for Warehouse Frontend

Comprehensive UI tests covering ~87 scenarios across all facility types.

## Setup

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install chromium
```

## Running Tests

```bash
# Run all tests
npx playwright test

# Run specific test file
npx playwright test auth.spec.ts

# Run with UI mode
npx playwright test --ui

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific test by grep
npx playwright test -g "should login"

# Debug mode
npx playwright test --debug
```

## Test Structure

```
e2e/
├── fixtures/          # Test fixtures
├── pages/             # Page Object Models
│   ├── login.page.ts
│   ├── dashboard.page.ts
│   ├── receipt.page.ts
│   ├── shipment.page.ts
│   └── issue.page.ts
├── tests/             # Test files
│   ├── auth.spec.ts              # Authentication tests (7)
│   ├── facility.spec.ts          # Facility selector tests (7)
│   ├── dc/                       # DC facility tests
│   │   ├── dc-dashboard.spec.ts  # (6)
│   │   ├── dc-receipts.spec.ts   # (10)
│   │   └── dc-shipments.spec.ts  # (10)
│   ├── wh/                       # WH facility tests
│   │   ├── wh-dashboard.spec.ts  # (5)
│   │   ├── wh-receipts.spec.ts   # (4)
│   │   ├── wh-shipments.spec.ts  # (4)
│   │   ├── wh-stock.spec.ts      # (4)
│   │   └── wh-inventory.spec.ts  # (5)
│   ├── pp/                       # PP facility tests
│   │   ├── pp-dashboard.spec.ts  # (4)
│   │   ├── pp-receipts.spec.ts   # (2)
│   │   └── pp-issues.spec.ts     # (6)
│   ├── e2e-flow.spec.ts          # Full E2E flows (2)
│   ├── negative.spec.ts          # Negative scenarios (7)
│   └── roles.spec.ts             # Role-based tests (4)
└── utils/             # Test utilities
    └── test-helpers.ts

Total: ~87 test scenarios
```

## Test Users

| Username | Password | Role | Facility |
|----------|----------|------|----------|
| admin | admin123 | SUPER_USER | - |
| dc_central_mgr | password123 | EMPLOYEE | DC-C-001 |
| wh_north_op | password123 | EMPLOYEE | WH-C-001 |
| wh_south_op | password123 | EMPLOYEE | WH-C-002 |
| pp_1_op | password123 | EMPLOYEE | PP-C-001 |
| pp_2_op | password123 | EMPLOYEE | PP-C-002 |

## Environment

Base URL: `http://192.168.1.74:31081` (default)

Override with environment variable:
```bash
BASE_URL=http://localhost:5173 npx playwright test
```

## Reports

After test run:
```bash
npx playwright show-report
```

## CI/CD

Tests are configured for CI with:
- 2 retries on failure
- Video recording on failure
- Screenshots on failure
- Trace on first retry

## Writing New Tests

1. Follow Page Object Model pattern
2. Use data-testid for selectors
3. Add helper functions to test-helpers.ts
4. Keep tests isolated and independent
5. Use descriptive test names

Example:
```typescript
test('DCR1: Receipts list loads', async ({ page }) => {
  await receiptPage.gotoList('dc')
  await page.waitForLoadState('networkidle')
  await expect(receiptPage.receiptsTable).toBeVisible({ timeout: 10000 })
})
```

## Troubleshooting

See `/home/flomaster/warehouse-master/docs/planning/waves/ui_testing.md` section 6 for common issues and solutions.
