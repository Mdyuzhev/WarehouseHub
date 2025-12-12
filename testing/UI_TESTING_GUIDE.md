# UI Testing Guide for Agents

## Критически важно: Порядок работы

**ВСЕГДА сначала изучай реальный код компонентов, потом пиши тесты!**

```
1. Прочитай Vue компонент → 2. Найди реальные data-testid → 3. Напиши тест
```

---

## Структура проекта

```
frontend/
├── src/
│   ├── components/        # Общие компоненты
│   │   ├── LoginPage.vue
│   │   ├── FacilitySelector.vue
│   │   └── documents/     # Компоненты документов
│   ├── views/             # Страницы по типам facility
│   │   ├── dc/            # Distribution Center
│   │   ├── wh/            # Warehouse
│   │   └── pp/            # Pickup Point
│   ├── stores/            # Pinia stores
│   └── services/          # API services
├── e2e/                   # Playwright тесты
│   ├── tests/             # Тест-файлы
│   ├── pages/             # Page Object Models
│   └── utils/             # Хелперы
└── playwright.config.ts
```

---

## Шаг 1: Изучение компонента

### Перед написанием теста ОБЯЗАТЕЛЬНО:

```bash
# 1. Найди нужный компонент
ls frontend/src/views/dc/
ls frontend/src/components/

# 2. Прочитай его полностью
cat frontend/src/views/dc/DCDashboard.vue

# 3. Найди все data-testid
grep -n "data-testid" frontend/src/views/dc/DCDashboard.vue
```

### Что искать в компоненте:

```vue
<!-- Ищи эти атрибуты -->
<div data-testid="dc-dashboard">           <!-- Контейнер страницы -->
<input data-testid="username">             <!-- Поля ввода -->
<button data-testid="login-button">        <!-- Кнопки -->
<select data-testid="facility-selector">   <!-- Селекторы -->
<table data-testid="receipts-table">       <!-- Таблицы -->
<router-link data-testid="receipts-link">  <!-- Навигация -->
```

### Если data-testid отсутствует:

**СНАЧАЛА добавь его в компонент, потом пиши тест!**

```vue
<!-- БЫЛО -->
<button @click="submit">Save</button>

<!-- СТАЛО -->
<button @click="submit" data-testid="save-button">Save</button>
```

---

## Шаг 2: Конфигурация Playwright

### playwright.config.ts — рабочая конфигурация:

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  expect: { timeout: 5000 },
  fullyParallel: false,
  retries: 2,  // ВАЖНО: retry для flaky тестов
  workers: 1,
  reporter: [['html'], ['list']],

  use: {
    baseURL: process.env.BASE_URL || 'http://192.168.1.74:31081',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true,

    // КРИТИЧНО для headless без GPU
    launchOptions: {
      args: [
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--single-process',
        '--no-zygote',
      ],
    },
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
```

---

## Шаг 3: Написание тестов

### Структура теста:

```typescript
import { test, expect } from '@playwright/test'
import { clearLocalStorage } from '../utils/test-helpers'

test.describe('Feature Name', () => {

  // Очистка перед каждым тестом
  test.beforeEach(async ({ page }) => {
    await clearLocalStorage(page)
  })

  test('TEST_ID: Description', async ({ page }) => {
    // 1. Navigate
    await page.goto('/login')

    // 2. Wait for element (ОБЯЗАТЕЛЬНО!)
    await page.waitForSelector('[data-testid="username"]', {
      state: 'visible',
      timeout: 10000
    })

    // 3. Interact
    await page.fill('[data-testid="username"]', 'admin')
    await page.fill('[data-testid="password"]', 'admin123')
    await page.click('[data-testid="login-button"]')

    // 4. Assert
    await expect(page).toHaveURL(/^(?!.*login).*$/)
  })
})
```

### Правила написания селекторов:

```typescript
// ПРАВИЛЬНО - используй data-testid
await page.click('[data-testid="save-button"]')
await page.fill('[data-testid="username"]')

// ДОПУСТИМО - для текстовых элементов
await page.click('text=Войти')
await page.click('button:has-text("Save")')

// ИЗБЕГАЙ - хрупкие селекторы
await page.click('.btn-primary')           // Класс может измениться
await page.click('button:nth-child(2)')    // Позиция может измениться
await page.click('#submit')                // ID редко используется в Vue
```

---

## Шаг 4: Page Object Model

### Создание Page Object:

```typescript
// e2e/pages/login.page.ts
import { Page, Locator } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly usernameInput: Locator
  readonly passwordInput: Locator
  readonly loginButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    this.page = page
    // Селекторы из РЕАЛЬНОГО компонента LoginPage.vue
    this.usernameInput = page.locator('[data-testid="username"]')
    this.passwordInput = page.locator('[data-testid="password"]')
    this.loginButton = page.locator('[data-testid="login-button"]')
    this.errorMessage = page.locator('[data-testid="error-message"]')
  }

  async goto() {
    await this.page.goto('/login')
    // ВАЖНО: ждём загрузки SPA
    await this.page.waitForLoadState('networkidle')
    await this.usernameInput.waitFor({ state: 'visible', timeout: 10000 })
  }

  async login(username: string, password: string) {
    await this.usernameInput.waitFor({ state: 'visible', timeout: 5000 })
    await this.usernameInput.fill(username)
    await this.passwordInput.fill(password)
    await this.loginButton.click()
  }
}
```

---

## Шаг 5: Хелперы

### test-helpers.ts:

```typescript
import { Page } from '@playwright/test'

export const users = {
  admin: { username: 'admin', password: 'admin123' },
  wh_north_op: { username: 'wh_north_op', password: 'password123' },
  pp_1_op: { username: 'pp_1_op', password: 'password123' },
}

// ВАЖНО: localStorage доступен только после навигации!
export async function clearLocalStorage(page: Page) {
  await page.goto('/login')  // Сначала навигация
  await page.evaluate(() => localStorage.clear())
}

export async function getLocalStorage(page: Page, key: string) {
  // Ключ токена в приложении: warehouse_auth_token
  return await page.evaluate((k) => localStorage.getItem(k), key)
}

export async function loginAs(page: Page, userKey: keyof typeof users) {
  const user = users[userKey]
  await page.goto('/login')
  await page.waitForSelector('[data-testid="username"]', { state: 'visible' })
  await page.fill('[data-testid="username"]', user.username)
  await page.fill('[data-testid="password"]', user.password)
  await page.click('[data-testid="login-button"]')
  await page.waitForURL(/^(?!.*login).*$/, { timeout: 10000 })
}
```

---

## Типичные ошибки и решения

### 1. GPU crash в headless

**Ошибка:**
```
GPU process isn't usable. Goodbye.
```

**Решение:**
```typescript
launchOptions: {
  args: ['--disable-gpu', '--single-process', '--no-zygote', '--no-sandbox']
}
```

### 2. localStorage недоступен

**Ошибка:**
```
SecurityError: Failed to read 'localStorage' from 'Window'
```

**Решение:**
```typescript
// НЕПРАВИЛЬНО
await page.evaluate(() => localStorage.clear())

// ПРАВИЛЬНО
await page.goto('/login')  // Сначала навигация!
await page.evaluate(() => localStorage.clear())
```

### 3. Элемент не найден (timeout)

**Ошибка:**
```
waiting for locator('[data-testid="xxx"]') to be visible
```

**Решение:**
1. Проверь что data-testid существует в компоненте
2. Убедись что компонент отрендерился:
```typescript
await page.waitForLoadState('networkidle')
await page.waitForSelector('[data-testid="xxx"]', { state: 'visible' })
```

### 4. CORS ошибка

**Ошибка:**
```
Access blocked by CORS policy
```

**Решение:**
- Dev frontend (31081) должен использовать Dev API (31080)
- Prod frontend (30081) должен использовать Prod API (30080)

### 5. Flaky тесты (нестабильные)

**Решение:**
```typescript
// В playwright.config.ts
retries: 2,

// В тесте - явные ожидания
await page.waitForSelector('[data-testid="table"]', { state: 'visible' })
await page.waitForLoadState('networkidle')
await page.waitForTimeout(500)  // Крайний случай
```

---

## Чеклист перед написанием теста

- [ ] Прочитал исходный код компонента
- [ ] Нашёл/добавил все нужные data-testid
- [ ] Проверил ключи localStorage (warehouse_auth_token, не token)
- [ ] Добавил waitFor для SPA элементов
- [ ] Использую правильный API URL для окружения
- [ ] Добавил retries в конфиг

---

## Команды запуска

```bash
# Все тесты
npm run test:e2e

# Один файл
npm run test:e2e -- e2e/tests/auth.spec.ts

# С UI (debug)
npm run test:e2e -- --ui

# С отчётом
npm run test:e2e -- --reporter=html
npx playwright show-report
```

---

## Реальные data-testid в проекте

### LoginPage.vue
- `data-testid="username"` — поле логина
- `data-testid="password"` — поле пароля
- `data-testid="login-button"` — кнопка входа
- `data-testid="error-message"` — сообщение об ошибке

### FacilitySelector.vue
- `data-testid="facility-selector"` — селектор объекта

### DCDashboard.vue
- `data-testid="dc-dashboard"` — контейнер
- `data-testid="receipts-count"` — счётчик приходных
- `data-testid="shipments-count"` — счётчик расходных
- `data-testid="receipts-link"` — ссылка на приходные
- `data-testid="shipments-link"` — ссылка на расходные
- `data-testid="new-receipt-link"` — создать приход
- `data-testid="new-shipment-link"` — создать расход

### DCReceiptCreate.vue
- `data-testid="supplier-input"` — поле поставщика
- `data-testid="product-select"` — выбор товара
- `data-testid="quantity-input"` — количество
- `data-testid="add-item-button"` — добавить позицию
- `data-testid="save-button"` — сохранить

### WHStockList.vue
- `data-testid="stock-table"` — таблица остатков
- `data-testid="filter-input"` — поиск
- `data-testid="low-stock-filter"` — фильтр низких остатков
- `data-testid="stock-row"` / `data-testid="low-stock-row"` — строки

---

## Итого: Алгоритм для агента

```
1. Получил задачу написать тест для страницы X
2. cat frontend/src/views/.../X.vue — читаю компонент
3. grep "data-testid" — ищу существующие селекторы
4. Если нет нужных — добавляю в компонент
5. Пишу тест с waitFor и правильными селекторами
6. Запускаю: npm run test:e2e -- e2e/tests/x.spec.ts
7. Если падает — смотрю скриншот в test-results/
8. Фиксю и повторяю
```
