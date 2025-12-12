package com.warehouse.ui.tests;

import com.warehouse.ui.config.BaseTest;
import com.warehouse.ui.pages.LoginPage;
import com.warehouse.ui.pages.ProductsPage;
import io.qameta.allure.*;
import org.junit.jupiter.api.*;

@Epic("Products Management")
@Feature("Products View")
@Tag("products")
public class ProductsTest extends BaseTest {

    private final LoginPage loginPage = new LoginPage();
    private final ProductsPage productsPage = new ProductsPage();

    @Test
    @Story("View Products")
    @DisplayName("Products section should be visible after login")
    @Severity(SeverityLevel.BLOCKER)
    void testProductsSectionVisible() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();
        productsPage.verifySectionVisible();
    }

    @Test
    @Story("View Products")
    @DisplayName("Products title should be visible")
    @Severity(SeverityLevel.CRITICAL)
    void testProductsTitleVisible() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();
        productsPage.verifyTitleVisible();
    }

    @Test
    @Story("View Products")
    @DisplayName("Products list should show items")
    @Severity(SeverityLevel.CRITICAL)
    void testProductsListVisible() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();
        productsPage.verifyListVisible();
    }

    @Test
    @Story("Admin Access")
    @DisplayName("Admin should see edit buttons")
    @Severity(SeverityLevel.CRITICAL)
    void testAdminCanSeeEditButtons() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();
        productsPage.verifyListVisible();
        Assertions.assertTrue(productsPage.isEditButtonVisible(), "Edit buttons should be visible for admin");
    }

    @Test
    @Story("Admin Access")
    @DisplayName("Admin should see Add Product navigation")
    @Severity(SeverityLevel.CRITICAL)
    void testAdminCanSeeAddProduct() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();
        Assertions.assertTrue(productsPage.isAddProductVisible(), "Add Product should be visible for admin");
    }
}
