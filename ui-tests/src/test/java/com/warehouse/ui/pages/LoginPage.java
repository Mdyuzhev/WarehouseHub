package com.warehouse.ui.pages;

import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.$$;

/**
 * Login Page Object for Warehouse application.
 */
public class LoginPage {

    private final SelenideElement usernameInput = $("input[placeholder*='Username'], input[name='username'], #username");
    private final SelenideElement passwordInput = $("input[type='password'], input[name='password'], #password");
    private final SelenideElement loginButton = $("button[type='submit'], .login-button, button:contains('Login')");
    private final SelenideElement errorMessage = $(".error-message, .alert-danger, [class*='error']");
    private final SelenideElement logoutButton = $(".logout-button, button:contains('Logout'), [class*='logout']");

    @Step("Open login page")
    public LoginPage openPage() {
        return this;
    }

    @Step("Enter username: {username}")
    public LoginPage enterUsername(String username) {
        usernameInput.shouldBe(visible).setValue(username);
        return this;
    }

    @Step("Enter password")
    public LoginPage enterPassword(String password) {
        passwordInput.shouldBe(visible).setValue(password);
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
}
