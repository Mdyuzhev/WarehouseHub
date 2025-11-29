package com.warehouse.ui.tests;

import com.warehouse.ui.config.BaseTest;
import com.warehouse.ui.pages.LoginPage;
import io.qameta.allure.*;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

@Epic("Authentication")
@Feature("Login")
@Tag("login")
public class LoginTest extends BaseTest {

    private final LoginPage loginPage = new LoginPage();

    @Test
    @Story("Valid Login")
    @DisplayName("Admin should be able to login with valid credentials")
    @Severity(SeverityLevel.BLOCKER)
    void testAdminLogin() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();
    }

    @Test
    @Story("Valid Login")
    @DisplayName("Manager should be able to login with valid credentials")
    @Severity(SeverityLevel.CRITICAL)
    void testManagerLogin() {
        loginPage.login(config.managerUsername(), config.managerPassword());
        loginPage.verifyLoginSuccess();
    }

    @Test
    @Story("Valid Login")
    @DisplayName("Employee should be able to login with valid credentials")
    @Severity(SeverityLevel.CRITICAL)
    void testEmployeeLogin() {
        loginPage.login(config.employeeUsername(), config.employeePassword());
        loginPage.verifyLoginSuccess();
    }

    @Test
    @Story("Invalid Login")
    @DisplayName("Login should fail with invalid password")
    @Severity(SeverityLevel.CRITICAL)
    void testInvalidPassword() {
        loginPage.login(config.adminUsername(), "wrongpassword");
        loginPage.verifyErrorDisplayed();
    }

    @Test
    @Story("Invalid Login")
    @DisplayName("Login should fail with non-existent user")
    @Severity(SeverityLevel.NORMAL)
    void testNonExistentUser() {
        loginPage.login("nonexistent", "password123");
        loginPage.verifyErrorDisplayed();
    }

    @Test
    @Story("Logout")
    @DisplayName("User should be able to logout")
    @Severity(SeverityLevel.CRITICAL)
    void testLogout() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();
        loginPage.logout();
        // After logout, login form should be visible again
        loginPage.enterUsername(""); // Just verify login form is accessible
    }
}
