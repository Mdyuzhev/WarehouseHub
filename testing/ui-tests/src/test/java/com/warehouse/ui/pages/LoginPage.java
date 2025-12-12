package com.warehouse.ui.pages;

import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;

/**
 * Page Object для страницы авторизации системы Warehouse.
 * Использует data-testid атрибуты для надёжной идентификации элементов.
 */
public class LoginPage {

    // Элементы формы входа
    private final SelenideElement usernameInput = $("[data-testid='username-input']");
    private final SelenideElement passwordInput = $("[data-testid='password-input']");
    private final SelenideElement loginButton = $("[data-testid='login-button']");
    private final SelenideElement errorMessage = $("[data-testid='error-message']");

    // Элементы навигации после входа
    private final SelenideElement logoutButton = $("[data-testid='logout-button']");
    private final SelenideElement navProducts = $("[data-testid='nav-products']");

    @Step("Ввести имя пользователя: {username}")
    public LoginPage enterUsername(String username) {
        usernameInput.shouldBe(visible, enabled).setValue(username);
        return this;
    }

    @Step("Ввести пароль (скрыт из соображений безопасности)")
    public LoginPage enterPassword(String password) {
        passwordInput.shouldBe(visible, enabled).setValue(password);
        return this;
    }

    @Step("Нажать кнопку 'Войти в систему'")
    public LoginPage clickLogin() {
        loginButton.shouldBe(visible, enabled).click();
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
    @SuppressWarnings("null")
    public LoginPage verifyErrorContains(String text) {
        errorMessage.shouldBe(visible).shouldHave(text(text));
        return this;
    }

    @Step("Проверить успешный вход в систему - отображается кнопка выхода")
    public void verifyLoginSuccess() {
        logoutButton.shouldBe(visible);
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
        logoutButton.shouldBe(visible, enabled).click();
    }
}
