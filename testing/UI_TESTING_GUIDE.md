# UI Testing Guide (Selenide)

Руководство по разработке UI тестов на Selenide для Warehouse.

---

## Содержание

1. [Критически важно](#критически-важно)
2. [Структура проекта](#структура-проекта)
3. [Добавление data-testid во Frontend](#добавление-data-testid-во-frontend)
4. [Селекторы и Fallback паттерны](#селекторы-и-fallback-паттерны)
5. [Хелперы (Selectors.java)](#хелперы-selectorsjava)
6. [Page Object Model](#page-object-model)
7. [Написание тестов](#написание-тестов)
8. [Деплой после изменений](#деплой-после-изменений)
9. [Запуск тестов](#запуск-тестов)
10. [Отчёты Allure](#отчёты-allure)
11. [Частые ошибки](#частые-ошибки)
12. [Чек-лист](#чек-лист)

---

## Критически важно

### Порядок работы

```
1. Прочитай Vue компонент
2. Найди/добавь data-testid
3. Пересобери и задеплой frontend
4. Напиши тест с fallback селекторами
5. Запусти тесты
6. Собери отчёт
```

### Золотые правила

| Правило | Почему |
|---------|--------|
| **Сначала frontend, потом тесты** | Тесты без data-testid = flaky тесты |
| **Всегда fallback селекторы** | Vue SPA медленно рендерит элементы |
| **Custom timeout для SPA** | 4 сек по умолчанию мало для SPA |
| **Деплой после ЛЮБЫХ изменений frontend** | Тесты работают с deployed версией |

---

## Структура проекта

```
testing/ui-tests/
├── src/test/java/com/warehouse/ui/
│   ├── config/
│   │   ├── BaseTest.java        # Базовый класс
│   │   ├── TestConfig.java      # URL, credentials
│   │   ├── TestUsers.java       # Тестовые пользователи
│   │   └── Selectors.java       # Централизованные селекторы
│   ├── pages/
│   │   ├── LoginPage.java
│   │   ├── DashboardPage.java
│   │   ├── ReceiptPage.java
│   │   ├── ShipmentPage.java
│   │   ├── IssuePage.java
│   │   └── InventoryPage.java
│   └── tests/
│       ├── LoginTest.java
│       ├── AuthTest.java
│       ├── FacilityTest.java
│       ├── DCTest.java
│       ├── WHTest.java
│       ├── PPTest.java
│       ├── NegativeTest.java
│       └── E2EFlowTest.java
├── src/test/resources/
│   └── test.properties
└── pom.xml
```

---

## Добавление data-testid во Frontend

### Шаг 1: Найди компонент

```bash
# Структура frontend
ls frontend/src/components/
ls frontend/src/views/dc/
ls frontend/src/views/wh/
ls frontend/src/views/pp/
```

### Шаг 2: Добавь data-testid

```vue
<!-- БЫЛО -->
<button @click="submit" class="btn-primary">Сохранить</button>
<input v-model="username" type="text" />
<select v-model="facility">...</select>

<!-- СТАЛО -->
<button @click="submit" class="btn-primary" data-testid="save-button">Сохранить</button>
<input v-model="username" type="text" data-testid="username" />
<select v-model="facility" data-testid="facility-selector">...</select>
```

### Naming Convention для data-testid

| Тип элемента | Паттерн | Пример |
|--------------|---------|--------|
| Кнопка | `{action}-button` | `save-button`, `login-button`, `approve-button` |
| Поле ввода | `{field}-input` или `{field}` | `username`, `quantity-input` |
| Селект | `{name}-selector` или `{name}-select` | `facility-selector`, `product-select` |
| Таблица | `{entity}-table` | `receipts-table`, `stock-table` |
| Ссылка | `{target}-link` | `receipts-link`, `nav-products` |
| Бейдж/статус | `status-badge` | `status-badge` |
| Форма | `{entity}-form` | `receipt-form`, `shipment-form` |
| Сообщение | `{type}-message` | `error-message`, `success-message` |
| Строка таблицы | `{entity}-row-{id}` | `product-row-1` |

### Существующие data-testid в проекте

#### App.vue / Навигация
```
data-testid="nav-products"      — ссылка на продукты
data-testid="nav-add-product"   — добавить продукт
data-testid="nav-analytics"     — аналитика
data-testid="nav-status"        — статус системы
data-testid="logout-button"     — кнопка выхода
```

#### LoginPage.vue
```
data-testid="username"          — поле логина
data-testid="password"          — поле пароля
data-testid="login-button"      — кнопка входа
data-testid="error-message"     — сообщение об ошибке
```

#### FacilitySelector.vue
```
data-testid="facility-selector"           — селектор объекта
data-testid="facility-code"               — код текущего объекта
data-testid="facility-option-{code}"      — опция (DC-C-001, WH-C-001, etc.)
```

#### Dashboard страницы
```
data-testid="dc-dashboard"       — контейнер DC дашборда
data-testid="wh-dashboard"       — контейнер WH дашборда
data-testid="pp-dashboard"       — контейнер PP дашборда
data-testid="receipts-count"     — счётчик приходных
data-testid="shipments-count"    — счётчик расходных
data-testid="receipts-link"      — ссылка на приходные
data-testid="shipments-link"     — ссылка на расходные
```

#### Формы документов
```
data-testid="receipt-form"       — форма прихода
data-testid="shipment-form"      — форма расхода
data-testid="issue-form"         — форма выдачи
data-testid="inventory-form"     — форма инвентаризации
data-testid="supplier-input"     — поле поставщика
data-testid="product-select"     — выбор товара
data-testid="quantity-input"     — количество
data-testid="save-button"        — сохранить
data-testid="approve-button"     — утвердить
data-testid="confirm-button"     — подтвердить
data-testid="status-badge"       — статус документа
```

---

## Селекторы и Fallback паттерны

### Почему нужны fallback селекторы

Vue SPA рендерит элементы динамически. Элемент может:
- Появиться с задержкой
- Иметь разные классы в разных состояниях
- Не иметь data-testid (legacy код)

### Синтаксис fallback селекторов

```java
// Selenide поддерживает CSS селекторы с запятой (OR)
$("[data-testid='login-button'], button[type='submit']")

// Несколько fallback вариантов
$("[data-testid='facility-selector'], .facility-selector, .dropdown-toggle")

// С классом и атрибутом
$("[data-testid='error-message'], .error-message, .error, .alert-danger")
```

### Best Practices

```java
// ПРАВИЛЬНО - data-testid + fallback
$("[data-testid='save-button'], button.btn-primary, button[type='submit']")

// ПРАВИЛЬНО - несколько вариантов для таблиц
$("[data-testid='receipts-table'], .receipts-page, table.data-table")

// НЕПРАВИЛЬНО - только класс (может измениться)
$(".btn-primary")

// НЕПРАВИЛЬНО - только один селектор без fallback
$("[data-testid='save-button']")
```

---

## Хелперы (Selectors.java)

### Зачем нужен централизованный класс селекторов

1. **DRY** - не дублировать селекторы в каждом тесте
2. **Единая точка изменений** - меняешь в одном месте
3. **Timeout management** - единые настройки ожидания
4. **Fallback patterns** - все fallback в одном месте

### Структура Selectors.java

```java
package com.warehouse.ui.config;

import com.codeborne.selenide.SelenideElement;
import java.time.Duration;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;

public class Selectors {

    // ==================== Timeouts ====================
    public static final Duration PAGE_LOAD_TIMEOUT = Duration.ofSeconds(15);
    public static final Duration ELEMENT_TIMEOUT = Duration.ofSeconds(10);

    // ==================== Auth Elements ====================
    public static SelenideElement username() {
        return $("#username, [data-testid='username'], [data-testid='username-input'], input[name='username']");
    }

    public static SelenideElement password() {
        return $("#password, [data-testid='password'], [data-testid='password-input'], input[name='password']");
    }

    public static SelenideElement loginButton() {
        return $("[data-testid='login-button'], button[type='submit']");
    }

    public static SelenideElement logoutButton() {
        return $("[data-testid='logout-button'], .logout-btn, button.logout");
    }

    public static SelenideElement errorMessage() {
        return $("[data-testid='error-message'], .error-message, .error, .alert-danger");
    }

    // ==================== Facility Elements ====================
    public static SelenideElement facilitySelector() {
        return $("[data-testid='facility-selector'], .facility-selector, .dropdown-toggle");
    }

    public static SelenideElement facilityCode() {
        return $("[data-testid='facility-code'], .facility-code");
    }

    public static SelenideElement facilityOption(String code) {
        return $("[data-testid='facility-option-" + code + "'], [data-facility='" + code + "']");
    }

    // ==================== Form Elements ====================
    public static SelenideElement statusBadge() {
        return $("[data-testid='status-badge'], .status-badge");
    }

    public static SelenideElement saveButton() {
        return $("[data-testid='save-button'], button[type='submit'], .btn-save");
    }

    public static SelenideElement approveButton() {
        return $("[data-testid='approve-button'], .btn-approve");
    }

    // ==================== Wait Helpers ====================
    public static void waitForFacilitySelector() {
        facilitySelector().shouldBe(visible, PAGE_LOAD_TIMEOUT);
    }

    public static void waitForLogout() {
        logoutButton().shouldBe(visible, PAGE_LOAD_TIMEOUT);
    }

    public static void waitForError() {
        errorMessage().shouldBe(visible, ELEMENT_TIMEOUT);
    }

    public static void waitForStatus() {
        statusBadge().shouldBe(visible, PAGE_LOAD_TIMEOUT);
    }

    // ==================== Composite Helpers ====================
    public static void loginAndSelectFacility(String username, String password,
                                               LoginPage loginPage, DashboardPage dashboardPage,
                                               String facilityCode) {
        loginPage.login(username, password);
        loginPage.verifyLoginSuccess();
        waitForFacilitySelector();
        dashboardPage.selectFacility(facilityCode);
        facilityCode().shouldHave(text(facilityCode), PAGE_LOAD_TIMEOUT);
    }
}
```

### Использование в тестах

```java
// В тесте - используем хелперы
import static com.warehouse.ui.config.Selectors.*;

@Test
void testLogin() {
    loginPage.login("admin", "admin123");
    waitForLogout();  // вместо $("[data-testid='logout-button']").shouldBe(visible)
    assertTrue(dashboardPage.isFacilitySelectorVisible());
}

@Test
void testSelectFacility() {
    loginAndSelectFacility("admin", "admin123", loginPage, dashboardPage, "DC-C-001");
    // Уже залогинен и выбран facility
}
```

---

## Page Object Model

### Структура Page Object

```java
package com.warehouse.ui.pages;

import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;
import java.time.Duration;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.open;

public class LoginPage {

    private static final Duration TIMEOUT = Duration.ofSeconds(10);

    // Селекторы с fallback
    private final SelenideElement usernameInput =
        $("#username, [data-testid='username'], input[name='username']");
    private final SelenideElement passwordInput =
        $("#password, [data-testid='password'], input[name='password']");
    private final SelenideElement loginButton =
        $("[data-testid='login-button'], button[type='submit']");
    private final SelenideElement errorMessage =
        $("[data-testid='error-message'], .error-message, .error");
    private final SelenideElement logoutButton =
        $("[data-testid='logout-button'], .logout-btn");

    @Step("Open login page")
    public LoginPage openPage() {
        open("/login");
        return this;
    }

    @Step("Login as {username}")
    public void login(String username, String password) {
        // Selenide click/setValue имеют built-in smart waiting
        usernameInput.setValue(username);
        passwordInput.setValue(password);
        loginButton.click();
    }

    @Step("Verify login success")
    public void verifyLoginSuccess() {
        // Custom timeout для SPA
        logoutButton.shouldBe(visible, TIMEOUT);
    }

    @Step("Verify error is displayed")
    public void verifyErrorDisplayed() {
        errorMessage.shouldBe(visible, TIMEOUT);
    }

    @Step("Check if error is visible")
    public boolean isErrorVisible() {
        return errorMessage.isDisplayed();
    }
}
```

### Правила Page Object

| Правило | Пример |
|---------|--------|
| Один класс = одна страница | `LoginPage`, `DashboardPage` |
| Методы возвращают this или void | `return this;` для chaining |
| Селекторы приватные | `private final SelenideElement` |
| @Step для Allure отчётов | `@Step("Login as {username}")` |
| Timeout через Duration | `Duration.ofSeconds(10)` |

---

## Написание тестов

### Базовый класс

```java
package com.warehouse.ui.config;

import com.codeborne.selenide.Configuration;
import com.codeborne.selenide.logevents.SelenideLogger;
import io.qameta.allure.selenide.AllureSelenide;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;

import static com.codeborne.selenide.Selenide.open;

public abstract class BaseTest {

    protected final TestConfig config = new TestConfig();

    @BeforeAll
    static void setupAll() {
        // Selenide configuration
        Configuration.browser = "chrome";
        Configuration.browserSize = "1920x1080";
        Configuration.headless = true;
        Configuration.timeout = 10000;  // 10 сек по умолчанию
        Configuration.pageLoadTimeout = 30000;

        // Remote WebDriver (Selenium Grid)
        Configuration.remote = "http://192.168.1.74:4444/wd/hub";

        // Allure integration
        SelenideLogger.addListener("AllureSelenide",
            new AllureSelenide()
                .screenshots(true)
                .savePageSource(true));
    }

    @BeforeEach
    void setup() {
        open(config.baseUrl());
    }
}
```

### Структура теста

```java
package com.warehouse.ui.tests;

import com.warehouse.ui.config.BaseTest;
import com.warehouse.ui.config.Selectors;
import com.warehouse.ui.config.TestUsers;
import com.warehouse.ui.pages.*;
import io.qameta.allure.*;
import org.junit.jupiter.api.*;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.*;
import static org.junit.jupiter.api.Assertions.*;

@Epic("Distribution Center")
@Feature("DC Operations")
@Tag("dc")
public class DCTest extends BaseTest {

    private final LoginPage loginPage = new LoginPage();
    private final DashboardPage dashboardPage = new DashboardPage();
    private final ReceiptPage receiptPage = new ReceiptPage();

    private void loginAndSelectDC() {
        Selectors.loginAndSelectFacility(
            TestUsers.ADMIN.username, TestUsers.ADMIN.password,
            loginPage, dashboardPage, "DC-C-001"
        );
    }

    @Test
    @Story("Dashboard")
    @DisplayName("DC1: Dashboard loads with statistics")
    @Severity(SeverityLevel.CRITICAL)
    void testDashboardLoadsWithStatistics() {
        loginAndSelectDC();

        dashboardPage.verifyReceiptsCountVisible();
        dashboardPage.verifyShipmentsCountVisible();

        String receiptsCount = dashboardPage.getReceiptsCount();
        assertNotNull(receiptsCount, "Receipts count should be visible");
    }

    @Test
    @Story("Receipts")
    @DisplayName("DCR3: Create Receipt - status DRAFT")
    @Severity(SeverityLevel.BLOCKER)
    void testCreateReceiptDraft() {
        loginAndSelectDC();

        receiptPage.openCreate("dc");
        Selectors.receiptForm().shouldBe(visible);

        receiptPage.fillSupplier("Test Supplier");
        receiptPage.selectProduct("1");
        receiptPage.fillQuantity("100");
        receiptPage.save();

        Selectors.waitForStatus();
        assertTrue(url().matches(".*/dc/receipts/\\d+"), "Should redirect to receipt detail");

        String status = receiptPage.getStatus();
        assertTrue(status.contains("DRAFT"), "Status should be DRAFT");
    }
}
```

---

## Деплой после изменений

### ВАЖНО: После ЛЮБЫХ изменений во frontend

```bash
# 1. Пересборка frontend
cd /home/flomaster/warehouse-master/frontend
docker build --no-cache -t warehouse-frontend:latest .

# 2. Загрузка в k3s
sudo k3s ctr images rm docker.io/library/warehouse-frontend:latest 2>/dev/null || true
docker save warehouse-frontend:latest | sudo k3s ctr images import -

# 3. Рестарт deployment
kubectl rollout restart deployment/warehouse-frontend -n warehouse-dev

# 4. Ожидание готовности (30-60 сек)
kubectl rollout status deployment/warehouse-frontend -n warehouse-dev --timeout=120s

# 5. Проверка health
curl -s http://192.168.1.74:31081/ | head -20
```

### Полный скрипт деплоя

```bash
#!/bin/bash
# deploy-frontend.sh

set -e

echo "=== Building frontend ==="
cd /home/flomaster/warehouse-master/frontend
docker build --no-cache -t warehouse-frontend:latest .

echo "=== Loading to k3s ==="
sudo k3s ctr images rm docker.io/library/warehouse-frontend:latest 2>/dev/null || true
docker save warehouse-frontend:latest | sudo k3s ctr images import -

echo "=== Restarting deployment ==="
kubectl rollout restart deployment/warehouse-frontend -n warehouse-dev
kubectl rollout status deployment/warehouse-frontend -n warehouse-dev --timeout=120s

echo "=== Health check ==="
sleep 5
curl -s http://192.168.1.74:31081/ | grep -q "Warehouse" && echo "Frontend OK" || echo "Frontend FAILED"

echo "=== Deploy complete ==="
```

---

## Запуск тестов

### UI тесты (Selenide)

```bash
cd /home/flomaster/warehouse-master/testing/ui-tests

# Все UI тесты
./mvnw test

# Конкретный класс
./mvnw test -Dtest="LoginTest"

# Несколько классов
./mvnw test -Dtest="LoginTest,AuthTest,DCTest"

# По тегу
./mvnw test -Dgroups="dc"

# Один тест из каждого класса (smoke)
./mvnw test -Dtest="LoginTest#testAdminLogin,AuthTest#testAdminLogin,DCTest#testDashboardLoadsWithStatistics,WHTest#testDashboardLoadsWithStatistics,PPTest#testDashboardLoadsWithStatistics"

# С другим URL
./mvnw test -Dbase.url=http://192.168.1.74:30081
```

### E2E API тесты (REST-assured)

```bash
cd /home/flomaster/warehouse-master/testing/e2e-tests

# Все E2E тесты
./mvnw test

# Конкретный класс
./mvnw test -Dtest="ReceiptsApiTest"
```

### Все тесты (UI + E2E)

```bash
# Полный прогон всех тестов
cd /home/flomaster/warehouse-master/testing

# UI тесты
cd ui-tests && ./mvnw test && cd ..

# E2E тесты
cd e2e-tests && ./mvnw test && cd ..
```

---

## Отчёты Allure

### Генерация отчёта

```bash
cd /home/flomaster/warehouse-master/testing/ui-tests

# Сгенерировать отчёт
./mvnw allure:report

# Открыть в браузере
./mvnw allure:serve
```

### Структура отчёта

```
target/
├── allure-results/          # Сырые результаты
│   ├── *-result.json
│   ├── *-attachment.png     # Скриншоты
│   └── *-attachment.html    # Page source
└── site/allure-maven-plugin/  # HTML отчёт
    └── index.html
```

### Полный отчёт по всем тестам

```bash
#!/bin/bash
# run-all-tests-with-report.sh

REPORT_DIR="/home/flomaster/warehouse-master/testing/reports/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$REPORT_DIR"

echo "=== Running UI Tests ==="
cd /home/flomaster/warehouse-master/testing/ui-tests
./mvnw test allure:report 2>&1 | tee "$REPORT_DIR/ui-tests.log"
cp -r target/site/allure-maven-plugin "$REPORT_DIR/ui-allure"

echo "=== Running E2E Tests ==="
cd /home/flomaster/warehouse-master/testing/e2e-tests
./mvnw test allure:report 2>&1 | tee "$REPORT_DIR/e2e-tests.log"
cp -r target/site/allure-maven-plugin "$REPORT_DIR/e2e-allure"

echo "=== Summary ==="
echo "UI Tests:"
grep -E "Tests run:|BUILD" "$REPORT_DIR/ui-tests.log" | tail -5
echo ""
echo "E2E Tests:"
grep -E "Tests run:|BUILD" "$REPORT_DIR/e2e-tests.log" | tail -5
echo ""
echo "Reports saved to: $REPORT_DIR"
```

---

## Частые ошибки

### 1. Element not found / Timeout

**Причина:** Элемент не успел отрендериться

```java
// НЕПРАВИЛЬНО
$("[data-testid='button']").click();  // Может упасть

// ПРАВИЛЬНО
$("[data-testid='button']").shouldBe(visible, Duration.ofSeconds(10)).click();

// ИЛИ используй хелпер
Selectors.waitForLogout();
```

### 2. NoSuchElementException для facility-selector

**Причина:** Frontend не задеплоен с FacilitySelector компонентом

```bash
# Проверь что FacilitySelector есть в HTML
curl -s http://192.168.1.74:31081/ | grep "facility-selector"

# Если нет — пересобери и задеплой frontend
cd frontend && docker build -t warehouse-frontend:latest . && ...
```

### 3. Stale Element Reference

**Причина:** DOM обновился после получения элемента

```java
// НЕПРАВИЛЬНО
SelenideElement btn = $("button");
// ... что-то меняет DOM ...
btn.click();  // StaleElementReferenceException

// ПРАВИЛЬНО - Selenide автоматически перезапрашивает элемент
$("button").click();
```

### 4. Тесты падают только в headless режиме

**Причина:** Timing issues или GPU проблемы

```java
// В BaseTest
Configuration.headless = true;

// Добавь Chrome аргументы
Configuration.browserCapabilities = new DesiredCapabilities();
Configuration.browserCapabilities.setCapability("goog:chromeOptions",
    Map.of("args", List.of(
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage"
    )));
```

### 5. Неверный facility для Issue Acts

**Issue Acts только для PP (Pickup Points)!**

```java
// НЕПРАВИЛЬНО
dashboardPage.selectFacility("DC-C-001");
issuePage.openCreate();  // 404 или ошибка

// ПРАВИЛЬНО
dashboardPage.selectFacility("PP-C-001");  // id >= 4
issuePage.openCreate();
```

---

## Чек-лист

### Перед написанием теста

- [ ] Прочитал Vue компонент
- [ ] Нашёл/добавил все нужные data-testid
- [ ] Пересобрал и задеплоил frontend
- [ ] Проверил что элемент появляется в браузере

### При написании теста

- [ ] Использую fallback селекторы
- [ ] Использую Selectors.java хелперы
- [ ] Добавил custom timeout для SPA элементов
- [ ] Добавил @Step, @Story, @Severity для Allure
- [ ] Тест независим (не зависит от порядка запуска)

### После написания теста

- [ ] Тест проходит локально
- [ ] Тест проходит в headless режиме
- [ ] Проверил Allure отчёт

---

## Quick Reference

### Selenide Conditions

```java
visible              // элемент видим
exist                // элемент в DOM
enabled              // элемент активен
text("foo")          // содержит текст
exactText("foo")     // точный текст
cssClass("active")   // имеет класс
attribute("href")    // имеет атрибут
value("text")        // значение input
```

### Selenide Actions

```java
click()              // клик (ждёт visible)
setValue("text")     // ввод текста (очищает)
append("text")       // добавить текст
clear()              // очистить
sendKeys(Keys.ENTER) // нажать клавишу
hover()              // навести мышь
doubleClick()        // двойной клик
```

### Selenide Waits

```java
// Условие с timeout
element.shouldBe(visible, Duration.ofSeconds(10));

// Ожидание исчезновения
element.shouldNotBe(visible, Duration.ofSeconds(5));

// Ожидание текста
element.shouldHave(text("Success"), Duration.ofSeconds(10));
```

### URLs

| Окружение | Frontend | API |
|-----------|----------|-----|
| Dev | http://192.168.1.74:31081 | http://192.168.1.74:31080 |
| Prod | http://192.168.1.74:30081 | http://192.168.1.74:30080 |

---

*Обновлено: 2025-12-13*

**Sources:**
- [Selenide Documentation](https://selenide.org/documentation.html)
- [Selenide Page Objects](https://selenide.org/documentation/page-objects.html)
- [Selenide Selectors Javadoc](https://selenide.org/javadoc/current/com/codeborne/selenide/Selectors.html)
- [Selenide Big Wait Theory](https://selenide.org/2019/12/20/advent-calendar-big-wait-theory/)
