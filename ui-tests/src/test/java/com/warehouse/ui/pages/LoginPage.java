package com.warehouse.ui.pages;

import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;

/**
 * Login Page Object for Warehouse application.
 * Uses data-testid attributes for reliable element selection.
 */
public class LoginPage {

    // Login form elements
    private final SelenideElement usernameInput = $("[data-testid='username-input']");
    private final SelenideElement passwordInput = $("[data-testid='password-input']");
    private final SelenideElement loginButton = $("[data-testid='login-button']");
    private final SelenideElement errorMessage = $("[data-testid='error-message']");

    // After login - navigation elements
    private final SelenideElement logoutButton = $("[data-testid='logout-button']");
    private final SelenideElement navProducts = $("[data-testid='nav-products']");

    @Step("Enter username: {username}")
    public LoginPage enterUsername(String username) {
        usernameInput.shouldBe(visible, enabled).setValue(username);
        return this;
    }

    @Step("Enter password")
    public LoginPage enterPassword(String password) {
        passwordInput.shouldBe(visible, enabled).setValue(password);
        return this;
    }

    @Step("Click login button")
    public LoginPage clickLogin() {
        loginButton.shouldBe(visible, enabled).click();
        return this;
    }

    @Step("Login as {username}")
    public void login(String username, String password) {
        enterUsername(username);
        enterPassword(password);
        clickLogin();
    }

    @Step("Verify error message is displayed")
    public LoginPage verifyErrorDisplayed() {
        errorMessage.shouldBe(visible);
        return this;
    }

    @Step("Verify error message contains: {text}")
    public LoginPage verifyErrorContains(String text) {
        errorMessage.shouldBe(visible).shouldHave(text(text));
        return this;
    }

    @Step("Verify login was successful")
    public void verifyLoginSuccess() {
        logoutButton.shouldBe(visible);
    }

    @Step("Check if logged in")
    public boolean isLoggedIn() {
        return logoutButton.isDisplayed();
    }

    @Step("Verify navigation is visible after login")
    public LoginPage verifyNavigationVisible() {
        navProducts.shouldBe(visible);
        return this;
    }

    @Step("Click logout button")
    public void logout() {
        logoutButton.shouldBe(visible, enabled).click();
    }
}
