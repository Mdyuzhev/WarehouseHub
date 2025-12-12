# Playwright UI Tests - Детальный отчет
**Дата:** 2025-12-12
**Проект:** Warehouse Management System
**Окружение:** Dev (192.168.1.74:31081)
**Статус:** ❌ BLOCKED - Критическая ошибка окружения

---

## 📊 Краткая сводка

| Метрика | Значение |
|---------|----------|
| **Всего тестов** | 87 |
| **Пройдено** | 0 ❌ |
| **Провалено** | 87 ❌ |
| **Пропущено** | 0 |
| **Длительность** | ~45 секунд |
| **Success Rate** | 0% |

### Update 1 (19:32 UTC)
**Fix Applied:** Добавлены launch args в playwright.config.ts
**Result:** ❌ Частичное улучшение - браузер запускается дольше, но всё равно крашится
**Root Cause:** GPU process всё ещё пытается запуститься и падает после 3 попыток
**Next Action:** Использовать xvfb-run для эмуляции X server

### Update 2 (19:35 UTC)
**Discovery:** Проверил `/home/flomaster/warehouse-frontend` - там тоже Playwright с теми же проблемами
**Проблема подтверждена:** Системный уровень - нет GPU драйверов
**Решение:** Требуется установка xvfb с sudo правами
**Status:** ❌ BLOCKED - требуются административные права для установки xvfb

---

## 🚨 Критическая проблема

### GPU Process Crash

**Симптомы:**
```
ERROR:content/browser/gpu/gpu_process_host.cc:1000] GPU process launch failed: error_code=1002
WARNING:content/browser/gpu/gpu_process_host.cc:1448] The GPU process has crashed 9 time(s)
FATAL:content/browser/gpu/gpu_data_manager_impl_private.cc:415] GPU process isn't usable. Goodbye.
```

**Причина:**
Chromium пытается запустить GPU процесс в headless окружении без графических драйверов.

**Типичные окружения с этой проблемой:**
- Docker контейнеры
- CI/CD серверы
- Серверы без X server
- WSL без GUI

**Влияние:**
Все 87 тестов падают с ошибкой `browser.newContext: Target page, context or browser has been closed`

---

## 🔧 Решение

### Вариант 1: Обновить Playwright Config (Рекомендуется)

Добавить аргументы для запуска браузера в `playwright.config.ts`:

```typescript
export default defineConfig({
  // ... existing config
  use: {
    baseURL: process.env.BASE_URL || 'http://192.168.1.74:31081',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    launchOptions: {
      args: [
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-accelerated-2d-canvas',
        '--disable-webgl',
      ],
    },
  },
})
```

### Вариант 2: Использовать Xvfb (Virtual Frame Buffer)

Установить и использовать Xvfb для эмуляции X server:

```bash
# Установка
sudo apt-get install xvfb

# Запуск тестов
xvfb-run npm run test:e2e
```

### Вариант 3: Использовать Docker с правильными capability

```dockerfile
# В Dockerfile для CI
RUN apt-get update && apt-get install -y \
    xvfb \
    libgtk-3-0 \
    libnotify-dev \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2

# В docker-compose.yml
services:
  playwright:
    environment:
      - DISPLAY=:99
    command: xvfb-run npm run test:e2e
```

---

## 📋 Детальный анализ по категориям

### 1. Authentication Tests (0/7 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| A1 | Login with valid credentials (admin) | ❌ FAIL | GPU crash |
| A2 | Login with invalid password | ❌ FAIL | GPU crash |
| A3 | Login with non-existent user | ❌ FAIL | GPU crash |
| A4 | Login user with facility (wh_north_op) | ❌ FAIL | GPU crash |
| A5 | Logout | ❌ FAIL | GPU crash |
| A6 | Access protected page without authentication | ❌ FAIL | GPU crash |
| A7 | Refresh page after login preserves session | ❌ FAIL | GPU crash |

**Потенциальные проблемы после исправления GPU:**
- ⚠️ Тестовые пользователи могут отличаться от ожидаемых (admin vs ivanov)
- ⚠️ data-testid могут отсутствовать на некоторых элементах формы

### 2. Facility Selector Tests (0/7 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| F1 | Selector visible after admin login | ❌ FAIL | GPU crash |
| F2 | Select DC facility | ❌ FAIL | GPU crash |
| F3 | Select WH facility | ❌ FAIL | GPU crash |
| F4 | Select PP facility | ❌ FAIL | GPU crash |
| F5 | Change facility (DC -> WH) | ❌ FAIL | GPU crash |
| F6 | Facility persists in localStorage | ❌ FAIL | GPU crash |
| F7 | User with facility does not see selector | ❌ FAIL | GPU crash |

**Потенциальные проблемы после исправления GPU:**
- ⚠️ FacilitySelector может работать иначе для пользователей с привязанным facility
- ⚠️ Dropdown навигация может потребовать корректировки селекторов

### 3. DC Dashboard Tests (0/6 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| DC1 | Dashboard loads with statistics | ❌ FAIL | GPU crash |
| DC2 | Click "Receipts" navigates to receipts list | ❌ FAIL | GPU crash |
| DC3 | Click "Shipments" navigates to shipments list | ❌ FAIL | GPU crash |
| DC4 | Click "New Receipt" navigates to create receipt | ❌ FAIL | GPU crash |
| DC5 | Click "New Shipment" navigates to create shipment | ❌ FAIL | GPU crash |
| DC6 | Statistics update after document creation | ❌ FAIL | GPU crash |

**Критические замечания:**
- ❗ DCDashboard.vue минималистичен - отсутствуют элементы для навигации
- ❗ Нет data-testid для receipts-count, shipments-count, links
- ❗ Потребуется доработка dashboard UI

### 4. DC Receipts Tests (0/10 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| DCR1 | Receipts list loads | ❌ FAIL | GPU crash |
| DCR2 | Click table row navigates to detail | ❌ FAIL | GPU crash |
| DCR3 | Create Receipt with items - status DRAFT | ❌ FAIL | GPU crash |
| DCR4 | Create Receipt without items shows validation error | ❌ FAIL | GPU crash |
| DCR5 | Receipt detail displays all fields | ❌ FAIL | GPU crash |
| DCR6 | Approve Receipt (DRAFT -> APPROVED) | ❌ FAIL | GPU crash |
| DCR7 | Confirm Receipt (APPROVED -> CONFIRMED) | ❌ FAIL | GPU crash |
| DCR8 | Complete Receipt (CONFIRMED -> COMPLETED) | ❌ FAIL | GPU crash |
| DCR9 | Cancel DRAFT Receipt removes it from list | ❌ FAIL | GPU crash |
| DCR10 | EMPLOYEE user cannot see Approve button | ❌ FAIL | GPU crash |

**Потенциальные проблемы после исправления GPU:**
- ⚠️ Форма создания Receipt может не иметь всех необходимых data-testid
- ⚠️ Селекторы product-select, quantity-input могут отсутствовать
- ⚠️ supplier-input data-testid нужно добавить

### 5. DC Shipments Tests (0/10 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| DCS1 | Shipments list loads | ❌ FAIL | GPU crash |
| DCS2 | Create Shipment to WH-C-001 - status DRAFT | ❌ FAIL | GPU crash |
| DCS3 | Create Shipment to PP-C-001 | ❌ FAIL | GPU crash |
| DCS4 | Create Shipment without destination shows error | ❌ FAIL | GPU crash |
| DCS5 | Shipment detail shows source and destination | ❌ FAIL | GPU crash |
| DCS6 | Approve Shipment (DRAFT -> APPROVED) | ❌ FAIL | GPU crash |
| DCS7 | Ship Shipment (APPROVED -> SHIPPED) | ❌ FAIL | GPU crash |
| DCS8 | Deliver Shipment (SHIPPED -> DELIVERED) | ❌ FAIL | GPU crash |
| DCS9 | Cancel DRAFT Shipment | ❌ FAIL | GPU crash |
| DCS10 | Cancel APPROVED Shipment releases stock | ❌ FAIL | GPU crash |

**Потенциальные проблемы после исправления GPU:**
- ⚠️ destination-select может потребовать data-testid
- ⚠️ source-facility и destination-facility элементы нужно проверить

### 6. WH Dashboard Tests (0/5 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| WH1 | Dashboard loads with warehouse statistics | ❌ FAIL | GPU crash |
| WH2 | Click "Receipts" navigates to incoming receipts | ❌ FAIL | GPU crash |
| WH3 | Click "Shipments" navigates to outgoing shipments | ❌ FAIL | GPU crash |
| WH4 | Click "Stock" navigates to stock view | ❌ FAIL | GPU crash |
| WH5 | Click "Inventory" navigates to inventory acts | ❌ FAIL | GPU crash |

**Критические замечания:**
- ❗ WHDashboard.vue минималистичен

### 7. WH Receipts Tests (0/4 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| WHR1 | Incoming receipts list loads (from DC) | ❌ FAIL | GPU crash |
| WHR2 | Receipt detail shows source facility (DC) | ❌ FAIL | GPU crash |
| WHR3 | Confirm Receipt updates stock | ❌ FAIL | GPU crash |
| WHR4 | COMPLETED Receipt hides action buttons | ❌ FAIL | GPU crash |

### 8. WH Shipments Tests (0/4 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| WHS1 | Outgoing shipments list loads (to PP) | ❌ FAIL | GPU crash |
| WHS2 | Create Shipment to PP-C-001 | ❌ FAIL | GPU crash |
| WHS3 | Approve + Ship Shipment | ❌ FAIL | GPU crash |
| WHS4 | Stock decreases after Ship | ❌ FAIL | GPU crash |

### 9. WH Stock Tests (0/4 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| WHST1 | Stock list loads with products and quantities | ❌ FAIL | GPU crash |
| WHST2 | Filter by product name | ❌ FAIL | GPU crash |
| WHST3 | Low stock items highlighted | ❌ FAIL | GPU crash |
| WHST4 | Quantity updates after receipt confirmation | ❌ FAIL | GPU crash |

**Потенциальные проблемы после исправления GPU:**
- ⚠️ stock-table data-testid нужно добавить в stock views
- ⚠️ filter-input может отсутствовать

### 10. WH Inventory Tests (0/5 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| WHI1 | Create Inventory Act with items from stock | ❌ FAIL | GPU crash |
| WHI2 | Fill actual quantities - difference calculated | ❌ FAIL | GPU crash |
| WHI3 | Approve Inventory Act (DRAFT -> APPROVED) | ❌ FAIL | GPU crash |
| WHI4 | Complete Inventory Act - stock corrected | ❌ FAIL | GPU crash |
| WHI5 | Delete DRAFT Inventory Act | ❌ FAIL | GPU crash |

**Потенциальные проблемы после исправления GPU:**
- ⚠️ actual-quantity-input data-testid нужно добавить
- ⚠️ difference отображение проверить

### 11. PP Dashboard Tests (0/4 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| PP1 | Dashboard loads with pickup point statistics | ❌ FAIL | GPU crash |
| PP2 | Click "Receipts" navigates to incoming receipts | ❌ FAIL | GPU crash |
| PP3 | Click "Issues" navigates to issue acts | ❌ FAIL | GPU crash |
| PP4 | Click "Stock" navigates to stock view | ❌ FAIL | GPU crash |

**Критические замечания:**
- ❗ PPDashboard.vue минималистичен

### 12. PP Receipts Tests (0/2 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| PPR1 | Incoming receipts list loads (from WH) | ❌ FAIL | GPU crash |
| PPR2 | Confirm Receipt updates PP stock | ❌ FAIL | GPU crash |

### 13. PP Issues Tests (0/6 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| PPI1 | Issue Acts list loads | ❌ FAIL | GPU crash |
| PPI2 | Create Issue Act with customerName | ❌ FAIL | GPU crash |
| PPI3 | Create Issue without customerName shows error | ❌ FAIL | GPU crash |
| PPI4 | Complete Issue Act - stock deducted | ❌ FAIL | GPU crash |
| PPI5 | Delete DRAFT Issue Act | ❌ FAIL | GPU crash |
| PPI6 | EMPLOYEE cannot delete Issue Act | ❌ FAIL | GPU crash |

**Потенциальные проблемы после исправления GPU:**
- ⚠️ customer-name-input data-testid нужно добавить
- ⚠️ issues-table data-testid нужно добавить

### 14. E2E Flow Tests (0/2 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| E2E1 | DC → WH → PP complete cycle | ❌ FAIL | GPU crash |
| E2E2 | Inventory correction | ❌ FAIL | GPU crash |

**Критические замечания:**
- ❗ Эти тесты требуют наличия тестовых данных
- ❗ Полный цикл может занять значительное время
- ❗ Потребует дополнительной настройки начального состояния

### 15. Negative Tests (0/7 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| N1 | Access /dc without DC facility redirects or shows error | ❌ FAIL | GPU crash |
| N2 | Access /wh without WH facility redirects or shows error | ❌ FAIL | GPU crash |
| N3 | Access /pp without PP facility redirects or shows error | ❌ FAIL | GPU crash |
| N4 | EMPLOYEE attempts to Approve - button hidden or 403 | ❌ FAIL | GPU crash |
| N5 | Ship without sufficient stock shows error | ❌ FAIL | GPU crash |
| N6 | Double click on Approve sends only one request | ❌ FAIL | GPU crash |
| N7 | Network error shows error message and allows retry | ❌ FAIL | GPU crash |

### 16. Roles Tests (0/4 passed)

| ID | Test | Status | Блокер |
|----|------|--------|---------|
| R1 | Admin - access all facility types and approve/cancel | ❌ FAIL | GPU crash |
| R2 | DC Manager (EMPLOYEE) - only DC routes, create/view works | ❌ FAIL | GPU crash |
| R3 | WH Operator (EMPLOYEE) - only WH routes, create/view works | ❌ FAIL | GPU crash |
| R4 | PP Operator (EMPLOYEE) - only PP routes, create/view works | ❌ FAIL | GPU crash |

---

## ✅ Что работает

### Инфраструктура
- ✅ Frontend запущен и доступен на http://192.168.1.74:31081
- ✅ HTML страница загружается корректно
- ✅ Playwright установлен и настроен
- ✅ Chromium браузер скачан

### Код тестов
- ✅ Все 87 тестов написаны
- ✅ Page Object Model реализован
- ✅ Test helpers созданы
- ✅ Структура тестов соответствует best practices

### Vue компоненты
- ✅ LoginPage.vue - data-testid добавлены
- ✅ FacilitySelector.vue - data-testid добавлены
- ✅ DocumentActions.vue - динамические data-testid
- ✅ DocumentStatusBadge.vue - status-badge
- ✅ DocumentList.vue - таблицы и строки
- ✅ App.vue - logout-button

---

## ❌ Что не работает

### Критические проблемы
1. **GPU Process Crash** - блокирует все 87 тестов
2. **Dashboard Views минималистичны** - отсутствуют элементы навигации и статистики
3. **Отсутствуют data-testid** в формах создания/редактирования документов

### data-testid, которые нужно добавить

#### Формы создания документов
```vue
<!-- Receipt Create Form -->
<input data-testid="supplier-input" />
<select data-testid="product-select" />
<input data-testid="quantity-input" />
<button data-testid="add-item-button" />
<button data-testid="save-button" />

<!-- Shipment Create Form -->
<select data-testid="destination-select" />
<select data-testid="product-select" />
<input data-testid="quantity-input" />

<!-- Issue Act Create Form -->
<input data-testid="customer-name-input" />

<!-- Inventory Act Form -->
<input data-testid="actual-quantity-input" />
<span data-testid="difference" />
```

#### Dashboard views
```vue
<!-- DC/WH/PP Dashboard -->
<div data-testid="receipts-count">{{ count }}</div>
<div data-testid="shipments-count">{{ count }}</div>
<a data-testid="receipts-link" href="/dc/receipts">Приходные</a>
<a data-testid="shipments-link" href="/dc/shipments">Расходные</a>
<a data-testid="stock-link" href="/wh/stock">Остатки</a>
<a data-testid="inventory-link" href="/wh/inventory">Инвентаризация</a>
<a data-testid="issues-link" href="/pp/issues">Выдачи</a>
```

#### Stock/Inventory views
```vue
<table data-testid="stock-table">
<input data-testid="filter-input" />
<tr data-testid="low-stock-row" />
```

---

## 📝 Action Items

### Высокий приоритет

1. **[P0] Исправить GPU crash**
   ```bash
   # Вариант A: Обновить playwright.config.ts (см. раздел "Решение")
   # Вариант B: Использовать xvfb-run
   sudo apt-get install xvfb
   xvfb-run npm run test:e2e
   ```

2. **[P0] Добавить data-testid в формы**
   - Receipt Create/Edit forms
   - Shipment Create/Edit forms
   - Issue Act Create form
   - Inventory Act form

3. **[P0] Доработать Dashboard views**
   - DCDashboard.vue - добавить навигацию и счётчики
   - WHDashboard.vue - добавить навигацию и счётчики
   - PPDashboard.vue - добавить навигацию и счётчики

### Средний приоритет

4. **[P1] Добавить data-testid в stock/inventory views**
   - stock-table
   - filter-input
   - low-stock-row

5. **[P1] Проверить тестовых пользователей**
   - Убедиться, что существуют: admin, dc_central_mgr, wh_north_op, pp_1_op
   - Пароли соответствуют ожиданиям

6. **[P1] Добавить data-testid для деталей документов**
   - source-facility
   - destination-facility

### Низкий приоритет

7. **[P2] Оптимизировать время выполнения**
   - Увеличить workers до 2-3 после стабилизации
   - Сократить timeouts где возможно

8. **[P2] Добавить скриншоты в отчёты**
   - Настроить автоматические скриншоты для failing тестов

9. **[P2] CI/CD интеграция**
   - Добавить в GitLab CI pipeline
   - Настроить artifacts для отчётов

---

## 🔄 Следующие шаги

### Немедленно (сегодня)

1. Исправить GPU crash в playwright.config.ts
2. Запустить тесты повторно
3. Собрать список реальных ошибок (не связанных с GPU)

### На этой неделе

4. Добавить все недостающие data-testid
5. Доработать Dashboard views
6. Запустить тесты снова и достичь 50%+ success rate

### В течение месяца

7. Довести success rate до 90%+
8. Интегрировать в CI/CD
9. Настроить автоматический запуск на каждый commit

---

## 📊 Прогноз после исправления

После исправления GPU crash ожидаемые результаты:

| Категория | Ожидаемый Success Rate | Причина |
|-----------|------------------------|----------|
| Auth | 40-60% | Могут быть проблемы с пользователями |
| Facility | 50-70% | Зависит от реализации selector |
| DC Dashboard | 20-30% | Нужна доработка UI |
| DC Receipts | 30-50% | Нужны data-testid в формах |
| DC Shipments | 30-50% | Нужны data-testid в формах |
| WH Tests | 30-40% | Dashboard + forms |
| PP Tests | 30-40% | Dashboard + forms |
| E2E Flow | 0-20% | Требует тестовых данных |
| Negative | 50-70% | Должны работать лучше |
| Roles | 40-60% | Зависит от реализации RBAC |

**Общий прогноз: 35-50% success rate после первого исправления**

---

## 💡 Рекомендации

### Для разработчиков

1. **Использовать data-testid везде**
   - Все интерактивные элементы должны иметь data-testid
   - Следовать convention: `{action}-button`, `{field}-input`

2. **Не менять существующие data-testid**
   - Это break тесты
   - Если нужно изменить - обновить тесты соответственно

3. **Тестировать локально перед commit**
   ```bash
   npm run test:e2e:ui  # интерактивный режим
   ```

### Для QA

1. **Запускать тесты на каждом deploy**
2. **Следить за success rate**
3. **Создавать issues для failing тестов**
4. **Обновлять тесты при изменении UI**

### Для DevOps

1. **Настроить CI/CD pipeline**
2. **Сохранять artifacts (videos, screenshots, reports)**
3. **Отправлять уведомления в Telegram при failures**

---

## 📚 Полезные ссылки

- [Playwright Documentation](https://playwright.dev/)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [UI Testing Guide](/docs/planning/waves/ui_testing.md)
- [Test README](/home/flomaster/warehouse-master/frontend/e2e/README.md)

---

## 🏁 Заключение

**Текущий статус:** ❌ BLOCKED
**Основная проблема:** GPU process crash в headless окружении
**Решение:** Обновить playwright.config.ts с правильными launch args
**ETA исправления:** 15 минут
**Ожидаемый результат после исправления:** 35-50% success rate

**Дальнейшие действия:**
1. Применить fix для GPU crash
2. Запустить тесты снова
3. Собрать реальную статистику failures
4. Приоритизировать и исправить реальные проблемы
5. Достичь 90%+ success rate

---

*Отчёт сгенерирован: 2025-12-12 19:31 UTC*
*Версия: 1.0*
*Автор: Claude Code (Playwright Test Runner)*
