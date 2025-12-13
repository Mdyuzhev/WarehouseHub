package com.warehouse.ui.pages;

import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import java.time.Duration;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;

/**
 * Page Object для страницы авторизации системы Warehouse.
 * Использует data-testid атрибуты для надёжной идентификации элементов.
 *
 * Best practices Selenide:
 * - setValue/click автоматически ждут элемент (smart waiting)
 * - shouldBe используется только для assertions, не перед действиями
 * - Custom timeout для медленных SPA страниц
 */
public class LoginPage {

    private static final Duration PAGE_LOAD_TIMEOUT = Duration.ofSeconds(15);

    // Элементы формы входа - используем несколько селекторов для надёжности
    private final SelenideElement usernameInput = $("#username, [data-testid='username'], input[name='username']");
    private final SelenideElement passwordInput = $("#password, [data-testid='password'], input[name='password']");
    private final SelenideElement loginButton = $("[data-testid='login-button'], button[type='submit']");
    private final SelenideElement errorMessage = $("[data-testid='error-message'], .error-message, .error");

    // Элементы навигации после входа
    private final SelenideElement logoutButton = $("[data-testid='logout-button'], .logout-btn");
    private final SelenideElement navProducts = $("[data-testid='nav-products']");

    @Step("Ввести имя пользователя: {username}")
    public LoginPage enterUsername(String username) {
        // Ждём загрузки Vue компонента с увеличенным timeout
        usernameInput.shouldBe(visible, PAGE_LOAD_TIMEOUT).setValue(username);
        return this;
    }

    @Step("Ввести пароль")
    public LoginPage enterPassword(String password) {
        // setValue сам ждёт элемент (smart waiting)
        passwordInput.setValue(password);
        return this;
    }

    @Step("Нажать кнопку 'Войти в систему'")
    public LoginPage clickLogin() {
        // click сам ждёт элемент (smart waiting)
        loginButton.click();
        return this;
    }

    @Step("Выполнить вход в систему под пользователем: {username}")
    public void login(String username, String password) {
        enterUsername(username);
        enterPassword(password);
        clickLogin();
    }

    @Step("Проверить отображение сообщения об ошибке авторизации")
    public LoginPage verifyErrorDisplayed() {
        errorMessage.shouldBe(visible);
        return this;
    }

    @Step("Проверить что сообщение об ошибке содержит текст: {text}")
    public LoginPage verifyErrorContains(String text) {
        errorMessage.shouldBe(visible).shouldHave(text(text));
        return this;
    }

    @Step("Проверить успешный вход в систему - отображается кнопка выхода")
    public void verifyLoginSuccess() {
        // Увеличенный timeout для ожидания редиректа и загрузки dashboard
        logoutButton.shouldBe(visible, PAGE_LOAD_TIMEOUT);
    }

    @Step("Проверить статус авторизации пользователя")
    public boolean isLoggedIn() {
        return logoutButton.isDisplayed();
    }

    @Step("Проверить отображение навигационного меню после входа")
    public LoginPage verifyNavigationVisible() {
        navProducts.shouldBe(visible);
        return this;
    }

    @Step("Нажать кнопку 'Выход' для завершения сессии")
    public void logout() {
        // click сам ждёт элемент
        logoutButton.click();
    }

    @Step("Проверить видимость сообщения об ошибке")
    public boolean isErrorVisible() {
        return errorMessage.isDisplayed();
    }
}
