package com.warehouse.e2e.tests;

import com.warehouse.e2e.base.BaseE2ETest;
import com.warehouse.e2e.data.TestData;
import com.warehouse.e2e.helpers.AuthHelper;
import com.warehouse.e2e.helpers.ProductHelper;
import io.qameta.allure.*;
import org.junit.jupiter.api.*;

import static org.hamcrest.Matchers.*;

/**
 * E2E тесты для ProductController.
 * Проверяет CRUD операции с продуктами и ролевой доступ.
 */
@Epic("Warehouse API")
@Feature("Products Management")
@DisplayName("Product Controller E2E Tests")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class ProductControllerE2ETest extends BaseE2ETest {

    private AuthHelper authHelper;
    private ProductHelper productHelper;

    @BeforeAll
    void setupHelpers() {
        authHelper = new AuthHelper(port);
        productHelper = new ProductHelper(port, authHelper);
    }

    // ==================== GET PRODUCTS TESTS ====================

    @Test
    @Order(1)
    @Story("View Products")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Получение списка продуктов авторизованным пользователем")
    @Description("Проверяет что любой авторизованный пользователь может получить список продуктов")
    void shouldReturnProducts_whenUserIsAuthenticated() {
        // Arrange - используем MANAGER (минимальные права)
        String token = authHelper.getToken(
                TestData.Users.MANAGER,
                TestData.Users.MANAGER_PASSWORD
        );

        // Act
        var response = productHelper.getAllProducts(token);

        // Assert
        response.then()
                .statusCode(200)
                .body("$", instanceOf(java.util.List.class))
                .body("size()", greaterThanOrEqualTo(0));
    }

    @Test
    @Order(2)
    @Story("View Products")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Ошибка доступа к продуктам без авторизации")
    @Description("Проверяет что неавторизованный пользователь не может получить список продуктов")
    void shouldReturnUnauthorized_whenNotAuthenticated() {
        // Act - запрос без токена
        var response = request()
                .when()
                .get("/api/products");

        // Assert
        response.then()
                .statusCode(401);
    }

    // ==================== CREATE PRODUCT TESTS ====================

    @Test
    @Order(3)
    @Story("Create Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Успешное создание продукта сотрудником")
    @Description("Проверяет что EMPLOYEE может создавать продукты")
    void shouldCreateProduct_whenUserIsEmployee() {
        // Arrange
        String token = authHelper.getToken(
                TestData.Users.EMPLOYEE,
                TestData.Users.EMPLOYEE_PASSWORD
        );
        String productName = TestData.Products.uniqueName("E2E Test");

        // Act
        var response = productHelper.createProduct(
                token,
                productName,
                TestData.Products.DEFAULT_QUANTITY,
                TestData.Products.DEFAULT_PRICE
        );

        // Assert
        response.then()
                .statusCode(anyOf(equalTo(200), equalTo(201)))
                .body("id", notNullValue())
                .body("name", equalTo(productName))
                .body("quantity", equalTo(TestData.Products.DEFAULT_QUANTITY))
                .body("price", equalTo((float) TestData.Products.DEFAULT_PRICE));

        // Attach product info to report
        Allure.attachment("Created Product", response.asString());
    }

    @Test
    @Order(4)
    @Story("Create Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Запрет создания продукта для менеджера")
    @Description("Проверяет что MANAGER не может создавать продукты (403 Forbidden)")
    void shouldReturnForbidden_whenManagerTriesToCreateProduct() {
        // Arrange
        String token = authHelper.getToken(
                TestData.Users.MANAGER,
                TestData.Users.MANAGER_PASSWORD
        );

        // Act
        var response = productHelper.createProduct(
                token,
                TestData.Products.uniqueName("Forbidden"),
                10,
                19.99
        );

        // Assert
        response.then()
                .statusCode(403);
    }

    // ==================== DELETE PRODUCT TESTS ====================

    @Test
    @Order(5)
    @Story("Delete Product")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Успешное удаление продукта сотрудником")
    @Description("Проверяет что EMPLOYEE может удалять продукты")
    void shouldDeleteProduct_whenUserIsEmployee() {
        // Arrange - создаём продукт для удаления
        String token = authHelper.getToken(
                TestData.Users.EMPLOYEE,
                TestData.Users.EMPLOYEE_PASSWORD
        );
        Long productId = productHelper.createTestProduct(token);
        Allure.parameter("productId", productId);

        // Act
        var response = productHelper.deleteProduct(token, productId);

        // Assert
        response.then()
                .statusCode(anyOf(equalTo(200), equalTo(204)));
    }

    @Test
    @Order(6)
    @Story("Delete Product")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Запрет удаления продукта для администратора")
    @Description("Проверяет что ADMIN не может удалять продукты (только управление пользователями)")
    void shouldReturnForbidden_whenAdminTriesToDeleteProduct() {
        // Arrange - создаём продукт от имени superuser
        String superToken = authHelper.getToken(
                TestData.Users.SUPERUSER,
                TestData.Users.SUPERUSER_PASSWORD
        );
        Long productId = productHelper.createTestProduct(superToken);

        String adminToken = authHelper.getToken(
                TestData.Users.ADMIN,
                TestData.Users.ADMIN_PASSWORD
        );
        Allure.parameter("productId", productId);

        // Act
        var response = productHelper.deleteProduct(adminToken, productId);

        // Assert
        response.then()
                .statusCode(403);
    }
}