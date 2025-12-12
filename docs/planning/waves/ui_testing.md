# UI Testing with Playwright — Инструкция

Руководство по написанию Playwright UI тестов для Warehouse Frontend.

---

## Содержание

1. [Настройка](#1-настройка)
2. [Структура тестов](#2-структура-тестов)
3. [Паттерны и хелперы](#3-паттерны-и-хелперы)
4. [Тестовые данные](#4-тестовые-данные)
5. [Сценарии для покрытия](#5-сценарии-для-покрытия)
6. [Решение проблем](#6-решение-проблем)
7. [Чек-лист готовности](#7-чек-лист-готовности)

---

## 1. Настройка

### Установка Playwright

```bash
cd frontend
npm init playwright@latest
# TypeScript: Yes
# Tests folder: e2e
# GitHub Actions: No
# Install browsers: Yes
```

### playwright.config.ts

```typescript
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  expect: { timeout: 5000 },
  fullyParallel: false,          // Тесты зависят друг от друга
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,                     // Один worker для последовательности
  reporter: [['html'], ['list']],
  use: {
    baseURL: process.env.BASE_URL || 'http://192.168.1.74:31081',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
})
```

### Структура папок

```
frontend/
├── e2e/
│   ├── fixtures/
│   │   └── auth.fixture.ts      # Фикстуры авторизации
│   ├── pages/
│   │   ├── login.page.ts        # Page Object: Login
│   │   ├── dashboard.page.ts    # Page Object: Dashboard
│   │   ├── receipt.page.ts      # Page Object: Receipt
│   │   ├── shipment.page.ts     # Page Object: Shipment
│   │   └── issue.page.ts        # Page Object: Issue Act
│   ├── tests/
│   │   ├── auth.spec.ts
│   │   ├── dc/
│   │   │   ├── dc-dashboard.spec.ts
│   │   │   ├── dc-receipts.spec.ts
│   │   │   └── dc-shipments.spec.ts
│   │   ├── wh/
│   │   │   ├── wh-dashboard.spec.ts
│   │   │   ├── wh-receipts.spec.ts
│   │   │   ├── wh-shipments.spec.ts
│   │   │   └── wh-inventory.spec.ts
│   │   ├── pp/
│   │   │   ├── pp-dashboard.spec.ts
│   │   │   ├── pp-receipts.spec.ts
│   │   │   └── pp-issues.spec.ts
│   │   └── e2e-flow.spec.ts     # Full flow test
│   └── utils/
│       └── test-helpers.ts
└── playwright.config.ts
```

---

## 2. Структура тестов

### Именование файлов

```
{feature}.spec.ts           # Основной файл теста
{feature}.page.ts           # Page Object
{feature}.fixture.ts        # Фикстуры
```

### Структура test файла

```typescript
import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages/login.page'

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup перед каждым тестом
  })

  test.afterEach(async ({ page }) => {
    // Cleanup после каждого теста
  })

  test('should do something', async ({ page }) => {
    // Arrange
    // Act
    // Assert
  })
})
```

### Page Object Pattern

```typescript
// pages/login.page.ts
import { Page, Locator } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly usernameInput: Locator
  readonly passwordInput: Locator
  readonly loginButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    this.page = page
    this.usernameInput = page.locator('[data-testid="username"]')
    this.passwordInput = page.locator('[data-testid="password"]')
    this.loginButton = page.locator('[data-testid="login-button"]')
    this.errorMessage = page.locator('[data-testid="error-message"]')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username)
    await this.passwordInput.fill(password)
    await this.loginButton.click()
  }
}
```

---

## 3. Паттерны и хелперы

### Auth Helper

```typescript
// utils/test-helpers.ts
import { Page } from '@playwright/test'

export const users = {
  admin: { username: 'admin', password: 'admin123' },
  dc_manager: { username: 'dc_central_mgr', password: 'password123' },
  wh_operator: { username: 'wh_north_op', password: 'password123' },
  pp_operator: { username: 'pp_1_op', password: 'password123' },
}

export async function loginAs(page: Page, userKey: keyof typeof users) {
  const user = users[userKey]
  await page.goto('/login')
  await page.fill('[data-testid="username"]', user.username)
  await page.fill('[data-testid="password"]', user.password)
  await page.click('[data-testid="login-button"]')
  await page.waitForURL(/^(?!.*login).*$/)  // URL не содержит "login"
}

export async function selectFacility(page: Page, facilityCode: string) {
  await page.click('[data-testid="facility-selector"]')
  await page.click(`text=${facilityCode}`)
  await page.waitForTimeout(500)  // Дождаться применения
}

export async function logout(page: Page) {
  await page.click('[data-testid="logout-button"]')
  await page.waitForURL('/login')
}
```

### Wait Helpers

```typescript
export async function waitForApi(page: Page) {
  await page.waitForLoadState('networkidle')
}

export async function waitForToast(page: Page, text: string) {
  await page.waitForSelector(`text=${text}`, { timeout: 5000 })
}

export async function waitForTableLoad(page: Page) {
  await page.waitForSelector('table tbody tr', { timeout: 10000 })
}
```

### Data-testid Convention

Все интерактивные элементы должны иметь `data-testid`:

| Элемент | Формат | Пример |
|---------|--------|--------|
| Кнопка | `{action}-button` | `login-button`, `approve-button` |
| Input | `{field}-input` или `{field}` | `username`, `quantity-input` |
| Ссылка | `{target}-link` | `receipts-link` |
| Таблица | `{entity}-table` | `receipts-table` |
| Строка таблицы | `{entity}-row` | `receipt-row` |
| Модальное окно | `{name}-modal` | `confirm-modal` |
| Selector | `{name}-selector` | `facility-selector` |
| Badge/Status | `status-badge` | `status-badge` |

---

## 4. Тестовые данные

### Пользователи

| User | Password | Role | Facility | Доступ |
|------|----------|------|----------|--------|
| admin | admin123 | SUPER_USER | - | Все |
| dc_central_mgr | password123 | EMPLOYEE | DC-C-001 | DC |
| wh_north_op | password123 | EMPLOYEE | WH-C-001 | WH |
| wh_south_op | password123 | EMPLOYEE | WH-C-002 | WH |
| pp_1_op | password123 | EMPLOYEE | PP-C-001 | PP |
| pp_2_op | password123 | EMPLOYEE | PP-C-002 | PP |

### Facilities

| ID | Code | Type | Parent |
|----|------|------|--------|
| 1 | DC-C-001 | DC | - |
| 2 | WH-C-001 | WH | DC-C-001 |
| 3 | WH-C-002 | WH | DC-C-001 |
| 4 | PP-C-001 | PP | WH-C-001 |
| 5 | PP-C-002 | PP | WH-C-001 |

### Products (для тестов)

| ID | Name | Для тестов |
|----|------|-----------|
| 1 | Test Product 1 | Основной |
| 2 | Test Product 2 | Альтернативный |

---

## 5. Сценарии для покрытия

### ЗАДАЧА: Написать тесты по всем сценариям ниже

Каждый сценарий = отдельный `test()` в соответствующем файле.

---

### 5.1 Аутентификация (`auth.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| A1 | Логин с валидными credentials (admin) | Редирект на `/`, показан FacilitySelector |
| A2 | Логин с невалидным паролем | Показана ошибка, остаёмся на `/login` |
| A3 | Логин с несуществующим пользователем | Показана ошибка |
| A4 | Логин пользователя с facility (wh_north_op) | Редирект на `/wh`, facility автовыбран |
| A5 | Logout | Редирект на `/login`, токен удалён |
| A6 | Доступ к защищённой странице без авторизации | Редирект на `/login` |
| A7 | Refresh страницы после логина | Сессия сохранена |

---

### 5.2 Facility Selector (`facility.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| F1 | Selector виден после логина admin | Dropdown с facilities |
| F2 | Выбор DC facility | Редирект на `/dc`, тема DC |
| F3 | Выбор WH facility | Редирект на `/wh`, тема WH |
| F4 | Выбор PP facility | Редирект на `/pp`, тема PP |
| F5 | Смена facility (DC → WH) | URL и тема меняются |
| F6 | Facility сохраняется в localStorage | После refresh facility выбран |
| F7 | Пользователь с facility не видит selector | Selector скрыт или disabled |

---

### 5.3 DC Dashboard (`dc/dc-dashboard.spec.ts`)

**Роль:** admin (выбрать DC-C-001) или dc_central_mgr

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| DC1 | Dashboard загружается | Статистика: receipts, shipments count |
| DC2 | Клик "Приходные накладные" | Переход на `/dc/receipts` |
| DC3 | Клик "Расходные накладные" | Переход на `/dc/shipments` |
| DC4 | Клик "Новый приход" | Переход на `/dc/receipts/create` |
| DC5 | Клик "Новая отгрузка" | Переход на `/dc/shipments/create` |
| DC6 | Статистика обновляется после создания документа | Счётчик увеличился |

---

### 5.4 DC Receipts (`dc/dc-receipts.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| DCR1 | Список приходных загружается | Таблица с документами |
| DCR2 | Клик на строку таблицы | Переход на `/dc/receipts/:id` |
| DCR3 | Создание Receipt: заполнить форму, сохранить | Receipt создан, status=DRAFT |
| DCR4 | Создание Receipt без items | Ошибка валидации |
| DCR5 | Детали Receipt: все поля отображаются | Номер, supplier, items, status |
| DCR6 | Approve Receipt (DRAFT → APPROVED) | Status изменился, кнопка Confirm появилась |
| DCR7 | Confirm Receipt (APPROVED → CONFIRMED) | Status изменился |
| DCR8 | Complete Receipt (CONFIRMED → COMPLETED) | Status=COMPLETED, кнопки скрыты |
| DCR9 | Cancel Receipt (DRAFT) | Receipt удалён из списка |
| DCR10 | Кнопка Approve скрыта для EMPLOYEE | Только SUPER_USER видит |

---

### 5.5 DC Shipments (`dc/dc-shipments.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| DCS1 | Список отгрузок загружается | Таблица с документами |
| DCS2 | Создание Shipment в WH-C-001 | Shipment создан, status=DRAFT |
| DCS3 | Создание Shipment в PP-C-001 | Shipment создан |
| DCS4 | Создание Shipment без destination | Ошибка валидации |
| DCS5 | Детали Shipment: source и destination отображаются | Коды facilities |
| DCS6 | Approve Shipment (DRAFT → APPROVED) | Status изменился |
| DCS7 | Ship Shipment (APPROVED → SHIPPED) | Status=SHIPPED |
| DCS8 | Deliver Shipment (SHIPPED → DELIVERED) | Status=DELIVERED |
| DCS9 | Cancel DRAFT Shipment | Shipment удалён |
| DCS10 | Cancel APPROVED Shipment | Shipment отменён, stock released |

---

### 5.6 WH Dashboard (`wh/wh-dashboard.spec.ts`)

**Роль:** admin (выбрать WH-C-001) или wh_north_op

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| WH1 | Dashboard загружается | Статистика склада |
| WH2 | Клик "Входящие" | Переход на `/wh/receipts` |
| WH3 | Клик "Исходящие" | Переход на `/wh/shipments` |
| WH4 | Клик "Остатки" | Переход на `/wh/stock` |
| WH5 | Клик "Инвентаризация" | Переход на `/wh/inventory` |

---

### 5.7 WH Receipts (`wh/wh-receipts.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| WHR1 | Список входящих загружается | Приходы от DC |
| WHR2 | Детали Receipt из DC | Показан source facility |
| WHR3 | Confirm Receipt | Status=CONFIRMED, stock updated |
| WHR4 | Просмотр COMPLETED Receipt | Все кнопки скрыты |

---

### 5.8 WH Shipments (`wh/wh-shipments.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| WHS1 | Список исходящих загружается | Отгрузки в PP |
| WHS2 | Создание Shipment в PP-C-001 | Shipment создан |
| WHS3 | Approve + Ship Shipment | Status=SHIPPED |
| WHS4 | Проверка stock после Ship | Quantity уменьшился |

---

### 5.9 WH Stock (`wh/wh-stock.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| WHST1 | Список остатков загружается | Таблица products + quantities |
| WHST2 | Фильтр по product name | Список фильтруется |
| WHST3 | Показ low stock items | Подсветка красным |
| WHST4 | Обновление после Receipt confirm | Quantity увеличился |

---

### 5.10 WH Inventory (`wh/wh-inventory.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| WHI1 | Создание Inventory Act | Act создан, items из stock |
| WHI2 | Заполнение actual quantities | Difference рассчитан |
| WHI3 | Approve Inventory Act | Status=APPROVED |
| WHI4 | Complete Inventory Act | Stock скорректирован |
| WHI5 | Delete DRAFT Inventory | Act удалён |

---

### 5.11 PP Dashboard (`pp/pp-dashboard.spec.ts`)

**Роль:** admin (выбрать PP-C-001) или pp_1_op

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| PP1 | Dashboard загружается | Статистика ПВЗ |
| PP2 | Клик "Поступления" | Переход на `/pp/receipts` |
| PP3 | Клик "Выдачи" | Переход на `/pp/issues` |
| PP4 | Клик "Остатки" | Переход на `/pp/stock` |

---

### 5.12 PP Receipts (`pp/pp-receipts.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| PPR1 | Список поступлений загружается | Приходы от WH |
| PPR2 | Confirm Receipt | Status=CONFIRMED, stock updated |

---

### 5.13 PP Issues (`pp/pp-issues.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| PPI1 | Список выдач загружается | Таблица Issue Acts |
| PPI2 | Создание Issue Act | Act создан, customerName заполнен |
| PPI3 | Создание без customerName | Ошибка валидации |
| PPI4 | Complete Issue Act | Status=COMPLETED, stock deducted |
| PPI5 | Delete DRAFT Issue | Act удалён |
| PPI6 | EMPLOYEE не может delete | Кнопка скрыта или disabled |

---

### 5.14 Full E2E Flow (`e2e-flow.spec.ts`)

| # | Сценарий | Описание |
|---|----------|----------|
| E2E1 | DC → WH → PP полный цикл | 1. DC создаёт Receipt от supplier → approve → confirm<br>2. DC создаёт Shipment в WH → approve → ship<br>3. WH confirm auto-receipt<br>4. WH создаёт Shipment в PP → approve → ship<br>5. PP confirm receipt<br>6. PP создаёт Issue → complete |
| E2E2 | Inventory correction | WH создаёт Inventory, корректирует stock |

---

### 5.15 Негативные сценарии (`negative.spec.ts`)

| # | Сценарий | Ожидаемый результат |
|---|----------|---------------------|
| N1 | Доступ к /dc без DC facility | Редирект или ошибка |
| N2 | Доступ к /wh без WH facility | Редирект или ошибка |
| N3 | Доступ к /pp без PP facility | Редирект или ошибка |
| N4 | EMPLOYEE пытается Approve | 403 или кнопка скрыта |
| N5 | Ship без достаточного stock | Ошибка API |
| N6 | Двойной клик на Approve | Только один запрос |
| N7 | Работа при потере сети | Показ ошибки, retry возможен |

---

### 5.16 Ролевое тестирование (`roles.spec.ts`)

| # | Роль | Проверить |
|---|------|-----------|
| R1 | admin | Доступ ко всем facility types, approve/cancel работает |
| R2 | dc_central_mgr | Только DC routes, create/view работает |
| R3 | wh_north_op | Только WH routes, create/view работает |
| R4 | pp_1_op | Только PP routes, create/view работает |

---

## 6. Решение проблем

### Проблема: Тест падает на waitForURL

**Симптом:** `Timeout waiting for URL`

**Причины и решения:**

```typescript
// 1. URL не совпадает точно
// НЕПРАВИЛЬНО:
await page.waitForURL('/dc')
// ПРАВИЛЬНО (учитывает query params):
await page.waitForURL(/\/dc/)

// 2. Редирект занимает время
// Добавить timeout:
await page.waitForURL('/dc', { timeout: 10000 })

// 3. API медленный
// Дождаться загрузки:
await page.waitForLoadState('networkidle')
```

---

### Проблема: Element not found

**Симптом:** `Locator not found` или `Element is not visible`

**Причины и решения:**

```typescript
// 1. Элемент ещё не появился
await page.waitForSelector('[data-testid="button"]', { state: 'visible' })

// 2. Элемент в shadow DOM
page.locator('[data-testid="button"]').first()

// 3. Элемент скрыт за модальным окном
await page.locator('.modal').waitFor({ state: 'hidden' })
await page.click('[data-testid="button"]')

// 4. Несколько элементов с одинаковым селектором
await page.locator('[data-testid="row"]').nth(0).click()
```

---

### Проблема: Flaky tests (нестабильные)

**Симптом:** Тест иногда проходит, иногда падает

**Решения:**

```typescript
// 1. Добавить явные ожидания
await page.waitForResponse(resp =>
  resp.url().includes('/api/receipts') && resp.status() === 200
)

// 2. Использовать waitForLoadState
await page.waitForLoadState('networkidle')

// 3. Retry механизм в config
retries: 2,

// 4. Изолировать тесты (не зависят друг от друга)
test.beforeEach(async ({ page }) => {
  // Fresh state
})
```

---

### Проблема: API возвращает 401/403

**Симптом:** Тесты падают с ошибкой авторизации

**Решения:**

```typescript
// 1. Токен истёк - перелогиниться
test.beforeEach(async ({ page }) => {
  await loginAs(page, 'admin')
})

// 2. Проверить что токен сохранён в localStorage
const token = await page.evaluate(() => localStorage.getItem('token'))
expect(token).toBeTruthy()

// 3. Rate limiting - добавить задержку между тестами
test.afterEach(async () => {
  await new Promise(r => setTimeout(r, 500))
})
```

---

### Проблема: Тест не видит изменения в DOM

**Симптом:** `Expected "APPROVED" but got "DRAFT"`

**Решения:**

```typescript
// 1. Дождаться обновления
await expect(page.locator('[data-testid="status"]')).toHaveText('APPROVED', {
  timeout: 5000
})

// 2. После действия дождаться API
await page.click('[data-testid="approve-button"]')
await page.waitForResponse(resp => resp.url().includes('/approve'))
await page.waitForTimeout(500)  // DOM update

// 3. Принудительно обновить страницу
await page.reload()
```

---

### Проблема: Селектор facility не работает

**Симптом:** `Cannot click on facility`

**Решения:**

```typescript
// 1. Dropdown не открылся
await page.click('[data-testid="facility-selector"]')
await page.waitForSelector('.dropdown-menu', { state: 'visible' })
await page.click('text=WH-C-001')

// 2. Элемент за пределами viewport
await page.locator('text=WH-C-001').scrollIntoViewIfNeeded()
await page.click('text=WH-C-001')

// 3. Использовать selectOption для <select>
await page.selectOption('[data-testid="facility-selector"]', 'WH-C-001')
```

---

### Проблема: Таблица пустая

**Симптом:** `No rows in table`

**Решения:**

```typescript
// 1. API ещё не ответил
await page.waitForResponse(resp => resp.url().includes('/api/receipts'))

// 2. Нет данных - создать тестовые
test.beforeAll(async ({ request }) => {
  // Создать тестовые данные через API
})

// 3. Неверный facility выбран
const facility = await page.locator('[data-testid="facility-code"]').textContent()
expect(facility).toBe('WH-C-001')
```

---

### Проблема: Модальное окно не закрывается

**Симптом:** `Modal blocks interaction`

**Решения:**

```typescript
// 1. Закрыть явно
await page.click('[data-testid="modal-close"]')
await page.locator('.modal').waitFor({ state: 'hidden' })

// 2. Нажать Escape
await page.keyboard.press('Escape')

// 3. Кликнуть вне модального окна
await page.click('.modal-backdrop')
```

---

### Проблема: Screenshot не показывает проблему

**Решения:**

```typescript
// 1. Включить video
use: {
  video: 'on',  // Всегда записывать видео
}

// 2. Включить trace
use: {
  trace: 'on',  // Всегда записывать trace
}

// 3. Добавить console.log перед падением
page.on('console', msg => console.log(msg.text()))
```

---

### Проблема: data-testid отсутствует в компоненте

**Симптом:** Нельзя найти элемент по `[data-testid="..."]`

**Решение:** Добавить атрибуты в Vue компоненты:

```vue
<!-- До -->
<button @click="handleSubmit">Submit</button>

<!-- После -->
<button data-testid="submit-button" @click="handleSubmit">Submit</button>
```

**Список компонентов для добавления data-testid:**

| Компонент | Элементы |
|-----------|----------|
| LoginPage.vue | username, password, login-button, error-message |
| FacilitySelector.vue | facility-selector, facility-option |
| DocumentList.vue | documents-table, document-row |
| DocumentDetail.vue | status-badge, approve-button, confirm-button, complete-button, cancel-button |
| DocumentActions.vue | approve-button, confirm-button, ship-button, deliver-button, complete-button, cancel-button, delete-button |
| Dashboard views | receipts-count, shipments-count, receipts-link, shipments-link |

---

## 7. Чек-лист готовности

### Перед написанием тестов

- [ ] Playwright установлен (`npx playwright --version`)
- [ ] Browsers установлены (`npx playwright install`)
- [ ] Frontend запущен на 31081
- [ ] API запущен на 31080
- [ ] Тестовые пользователи работают (проверить login)
- [ ] data-testid добавлены в компоненты

### Структура проекта

- [ ] Папка `e2e/` создана
- [ ] `playwright.config.ts` настроен
- [ ] `utils/test-helpers.ts` создан
- [ ] Page Objects созданы

### Перед commit

- [ ] Все тесты проходят локально (`npx playwright test`)
- [ ] Нет захардкоженных данных (ID, tokens)
- [ ] Page Objects используются
- [ ] Тесты изолированы (не зависят от порядка)
- [ ] Screenshots/videos не в git (добавить в .gitignore)

### После написания

- [ ] Все 70+ сценариев покрыты
- [ ] Все роли протестированы
- [ ] Все state transitions протестированы
- [ ] Негативные сценарии есть
- [ ] CI pipeline настроен (опционально)

---

## Команды запуска

```bash
# Все тесты
npx playwright test

# Конкретный файл
npx playwright test auth.spec.ts

# Конкретный тест
npx playwright test -g "should login"

# С UI
npx playwright test --ui

# Debug режим
npx playwright test --debug

# Генерация кода
npx playwright codegen http://192.168.1.74:31081

# Отчёт
npx playwright show-report
```

---

## Приоритет написания

| Приоритет | Файл | Сценариев |
|-----------|------|-----------|
| 1 | auth.spec.ts | 7 |
| 2 | facility.spec.ts | 7 |
| 3 | dc/dc-dashboard.spec.ts | 6 |
| 4 | dc/dc-receipts.spec.ts | 10 |
| 5 | dc/dc-shipments.spec.ts | 10 |
| 6 | wh/wh-dashboard.spec.ts | 5 |
| 7 | wh/wh-receipts.spec.ts | 4 |
| 8 | wh/wh-shipments.spec.ts | 4 |
| 9 | wh/wh-stock.spec.ts | 4 |
| 10 | wh/wh-inventory.spec.ts | 5 |
| 11 | pp/pp-dashboard.spec.ts | 4 |
| 12 | pp/pp-receipts.spec.ts | 2 |
| 13 | pp/pp-issues.spec.ts | 6 |
| 14 | e2e-flow.spec.ts | 2 |
| 15 | negative.spec.ts | 7 |
| 16 | roles.spec.ts | 4 |
| **Total** | | **~87** |

---

*Последнее обновление: 2025-12-12*
