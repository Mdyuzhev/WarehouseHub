package com.warehouse.ui.tests;

import com.warehouse.ui.config.BaseTest;
import com.warehouse.ui.pages.LoginPage;
import com.warehouse.ui.pages.ProductsPage;
import io.qameta.allure.*;
import org.junit.jupiter.api.*;

import java.util.UUID;

@Epic("Products Management")
@Feature("Products CRUD")
@Tag("products")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ProductsTest extends BaseTest {

    private final LoginPage loginPage = new LoginPage();
    private final ProductsPage productsPage = new ProductsPage();

    private static final String TEST_PRODUCT_PREFIX = "TestProduct_";
    private String testProductName;

    @BeforeEach
    void loginAsAdmin() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        testProductName = TEST_PRODUCT_PREFIX + UUID.randomUUID().toString().substring(0, 8);
    }

    @Test
    @Order(1)
    @Story("View Products")
    @DisplayName("Products table should be visible after login")
    @Severity(SeverityLevel.BLOCKER)
    void testProductsTableVisible() {
        productsPage.verifyTableVisible();
    }

    @Test
    @Order(2)
    @Story("Create Product")
    @DisplayName("Admin should be able to create a new product")
    @Severity(SeverityLevel.CRITICAL)
    void testCreateProduct() {
        int initialCount = productsPage.getProductsCount();

        productsPage.createProduct(
                testProductName,
                100,
                29.99,
                "Electronics",
                "Test product description"
        );

        productsPage.verifyProductExists(testProductName);
        Assertions.assertTrue(productsPage.getProductsCount() >= initialCount);
    }

    @Test
    @Order(3)
    @Story("Search Products")
    @DisplayName("User should be able to search products")
    @Severity(SeverityLevel.NORMAL)
    void testSearchProduct() {
        // First create a product to search for
        productsPage.createProduct(testProductName, 50, 19.99, "Test", "Searchable");

        productsPage.searchProduct(testProductName);
        productsPage.verifyProductExists(testProductName);
    }

    @Test
    @Order(4)
    @Story("Update Product")
    @DisplayName("Admin should be able to update a product")
    @Severity(SeverityLevel.CRITICAL)
    void testUpdateProduct() {
        // Create product first
        productsPage.createProduct(testProductName, 50, 19.99, "Test", "Original");

        // Update it
        productsPage.searchProduct(testProductName);
        productsPage.clickEditProduct(0);
        productsPage.fillProductForm(
                testProductName + "_Updated",
                75,
                24.99,
                "Updated",
                "Updated description"
        );
        productsPage.saveProduct();

        productsPage.verifyProductExists(testProductName + "_Updated");
    }

    @Test
    @Order(5)
    @Story("Delete Product")
    @DisplayName("Admin should be able to delete a product")
    @Severity(SeverityLevel.CRITICAL)
    void testDeleteProduct() {
        // Create product first
        productsPage.createProduct(testProductName, 50, 19.99, "Test", "To be deleted");

        productsPage.searchProduct(testProductName);
        productsPage.clickDeleteProduct(0);
        productsPage.confirmDelete();

        productsPage.verifyProductNotExists(testProductName);
    }
}
