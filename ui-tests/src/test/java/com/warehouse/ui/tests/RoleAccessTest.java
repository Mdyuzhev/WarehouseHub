package com.warehouse.ui.tests;

import com.warehouse.ui.config.BaseTest;
import com.warehouse.ui.pages.LoginPage;
import com.warehouse.ui.pages.ProductsPage;
import io.qameta.allure.*;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;

@Epic("Authorization")
@Feature("Role-Based Access Control")
@Tag("rbac")
public class RoleAccessTest extends BaseTest {

    private final LoginPage loginPage = new LoginPage();
    private final ProductsPage productsPage = new ProductsPage();

    @Test
    @Story("Admin Access")
    @DisplayName("Admin should have full access to products")
    @Severity(SeverityLevel.CRITICAL)
    void testAdminFullAccess() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();

        // Admin should see products section
        productsPage.verifySectionVisible();

        // Admin should see Add Product link
        Assertions.assertTrue(productsPage.isAddProductVisible(), "Admin should see Add Product");

        // Admin should see Edit buttons
        Assertions.assertTrue(productsPage.isEditButtonVisible(), "Admin should see Edit buttons");

        // Admin should see Delete buttons
        Assertions.assertTrue(productsPage.isDeleteButtonVisible(), "Admin should see Delete buttons");
    }

    @Test
    @Story("Manager Access")
    @DisplayName("Manager should be able to view and edit products")
    @Severity(SeverityLevel.CRITICAL)
    void testManagerAccess() {
        loginPage.login(config.managerUsername(), config.managerPassword());
        loginPage.verifyLoginSuccess();

        // Manager should see products section
        productsPage.verifySectionVisible();

        // Manager should see Add Product link
        Assertions.assertTrue(productsPage.isAddProductVisible(), "Manager should see Add Product");

        // Manager should see Edit buttons
        Assertions.assertTrue(productsPage.isEditButtonVisible(), "Manager should see Edit buttons");
    }

    @Test
    @Story("Employee Access")
    @DisplayName("Employee should only have read access")
    @Severity(SeverityLevel.CRITICAL)
    void testEmployeeReadOnly() {
        loginPage.login(config.employeeUsername(), config.employeePassword());
        loginPage.verifyLoginSuccess();

        // Employee should see products section
        productsPage.verifySectionVisible();

        // Employee should NOT see Add Product link
        Assertions.assertFalse(productsPage.isAddProductVisible(), "Employee should NOT see Add Product");

        // Employee should NOT see Edit buttons
        Assertions.assertFalse(productsPage.isEditButtonVisible(), "Employee should NOT see Edit buttons");

        // Employee should NOT see Delete buttons
        Assertions.assertFalse(productsPage.isDeleteButtonVisible(), "Employee should NOT see Delete buttons");
    }

    @Test
    @Story("Unauthorized Access")
    @DisplayName("Login page should be shown for unauthenticated users")
    @Severity(SeverityLevel.BLOCKER)
    void testUnauthenticatedRedirect() {
        // When opening the app without authentication
        // Login form should be visible (since app redirects to login)
        $("[data-testid='username-input']").shouldBe(visible);
        $("[data-testid='password-input']").shouldBe(visible);
        $("[data-testid='login-button']").shouldBe(visible);
    }
}
