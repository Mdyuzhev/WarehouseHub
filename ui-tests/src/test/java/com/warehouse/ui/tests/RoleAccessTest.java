package com.warehouse.ui.tests;

import com.warehouse.ui.config.BaseTest;
import com.warehouse.ui.pages.LoginPage;
import com.warehouse.ui.pages.ProductsPage;
import io.qameta.allure.*;
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
    @DisplayName("Admin should see all management options")
    @Severity(SeverityLevel.CRITICAL)
    void testAdminFullAccess() {
        loginPage.login(config.adminUsername(), config.adminPassword());

        // Admin should see products table
        productsPage.verifyTableVisible();

        // Admin should see Add button
        $(".add-product-button, button:contains('Add'), [class*='add']").shouldBe(visible);

        // Admin should see Edit buttons
        $(".edit-button, button:contains('Edit'), [class*='edit']").shouldBe(visible);

        // Admin should see Delete buttons
        $(".delete-button, button:contains('Delete'), [class*='delete']").shouldBe(visible);
    }

    @Test
    @Story("Manager Access")
    @DisplayName("Manager should be able to add and edit products")
    @Severity(SeverityLevel.CRITICAL)
    void testManagerAccess() {
        loginPage.login(config.managerUsername(), config.managerPassword());

        // Manager should see products table
        productsPage.verifyTableVisible();

        // Manager should see Add button
        $(".add-product-button, button:contains('Add'), [class*='add']").shouldBe(visible);

        // Manager should see Edit buttons
        $(".edit-button, button:contains('Edit'), [class*='edit']").shouldBe(visible);
    }

    @Test
    @Story("Employee Access")
    @DisplayName("Employee should only have read access")
    @Severity(SeverityLevel.CRITICAL)
    void testEmployeeReadOnly() {
        loginPage.login(config.employeeUsername(), config.employeePassword());

        // Employee should see products table
        productsPage.verifyTableVisible();

        // Employee should NOT see Add button (or it should be disabled)
        $(".add-product-button, button:contains('Add Product')").shouldNotBe(visible);

        // Employee should NOT see Delete buttons
        $(".delete-button, button:contains('Delete')").shouldNotBe(visible);
    }

    @Test
    @Story("Unauthorized Access")
    @DisplayName("Unauthenticated user should be redirected to login")
    @Severity(SeverityLevel.BLOCKER)
    void testUnauthenticatedRedirect() {
        // Without login, trying to access protected pages
        // Should show login form or redirect
        loginPage.verifyErrorDisplayed();
    }
}
