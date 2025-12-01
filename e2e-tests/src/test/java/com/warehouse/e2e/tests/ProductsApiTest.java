package com.warehouse.e2e.tests;

import com.warehouse.e2e.base.BaseE2ETest;
import io.qameta.allure.*;
import org.junit.jupiter.api.*;

import java.util.Map;
import java.util.UUID;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

/**
 * E2E тесты для Products API.
 * Проверяет CRUD операции и ролевой доступ.
 */
@Epic("Warehouse API")
@Feature("Products Management")
@DisplayName("Products API Tests")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ProductsApiTest extends BaseE2ETest {

    private static Integer createdProductId;
    private static String testProductName;

    // ===========================================
    // GET PRODUCTS - Позитивные сценарии
    // ===========================================

    @Test
    @Order(1)
    @Story("Get Products")
    @Severity(SeverityLevel.BLOCKER)
    @DisplayName("Получение списка продуктов (авторизован)")
    void getProductsAuthenticated() {
        authRequest(getEmployeeToken())
        .when()
            .get("/api/products")
        .then()
            .statusCode(200)
            .body("$", instanceOf(java.util.List.class));
    }

    @Test
    @Order(2)
    @Story("Get Products")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Все роли могут просматривать продукты")
    void allRolesCanViewProducts() {
        // Superuser
        authRequest(getSuperuserToken())
            .when().get("/api/products")
            .then().statusCode(200);

        // Admin
        authRequest(getAdminToken())
            .when().get("/api/products")
            .then().statusCode(200);

        // Manager
        authRequest(getManagerToken())
            .when().get("/api/products")
            .then().statusCode(200);

        // Employee
        authRequest(getEmployeeToken())
            .when().get("/api/products")
            .then().statusCode(200);

        // Analyst
        authRequest(getAnalystToken())
            .when().get("/api/products")
            .then().statusCode(200);
    }

    // ===========================================
    // GET PRODUCTS - Негативные сценарии
    // ===========================================

    @Test
    @Order(3)
    @Story("Get Products")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Получение продуктов без токена возвращает 403")
    void getProductsWithoutToken() {
        request()
        .when()
            .get("/api/products")
        .then()
            .statusCode(403);
    }

    @Test
    @Order(4)
    @Story("Get Products")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Получение продуктов с невалидным токеном возвращает 403")
    void getProductsWithInvalidToken() {
        authRequest("invalid.token.here")
        .when()
            .get("/api/products")
        .then()
            .statusCode(403);
    }

    // ===========================================
    // CREATE PRODUCT - Позитивные сценарии
    // ===========================================

    @Test
    @Order(10)
    @Story("Create Product")
    @Severity(SeverityLevel.BLOCKER)
    @DisplayName("Employee создаёт продукт успешно")
    void employeeCreatesProduct() {
        testProductName = "E2E Test Product " + UUID.randomUUID().toString().substring(0, 8);

        createdProductId = authRequest(getEmployeeToken())
            .body(Map.of(
                "name", testProductName,
                "quantity", 100,
                "price", 49.99
            ))
        .when()
            .post("/api/products")
        .then()
            .statusCode(201)
            .body("id", notNullValue())
            .body("name", equalTo(testProductName))
            .body("quantity", equalTo(100))
            .body("price", equalTo(49.99F))
            .extract()
            .path("id");

        Allure.attachment("Created Product ID", String.valueOf(createdProductId));
    }

    @Test
    @Order(11)
    @Story("Create Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Superuser создаёт продукт успешно")
    void superuserCreatesProduct() {
        String name = "Superuser Product " + UUID.randomUUID().toString().substring(0, 8);

        Integer id = authRequest(getSuperuserToken())
            .body(Map.of("name", name, "quantity", 50, "price", 99.99))
        .when()
            .post("/api/products")
        .then()
            .statusCode(201)
            .body("id", notNullValue())
            .extract()
            .path("id");

        // Удаляем созданный продукт
        authRequest(getSuperuserToken())
            .when().delete("/api/products/" + id)
            .then().statusCode(anyOf(is(200), is(204)));
    }

    // ===========================================
    // CREATE PRODUCT - Негативные сценарии
    // ===========================================

    @Test
    @Order(12)
    @Story("Create Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Manager НЕ может создавать продукты (403)")
    void managerCannotCreateProduct() {
        authRequest(getManagerToken())
            .body(Map.of("name", "Forbidden Product", "quantity", 10, "price", 10.0))
        .when()
            .post("/api/products")
        .then()
            .statusCode(403);
    }

    @Test
    @Order(13)
    @Story("Create Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Admin НЕ может создавать продукты (403)")
    void adminCannotCreateProduct() {
        authRequest(getAdminToken())
            .body(Map.of("name", "Admin Product", "quantity", 10, "price", 10.0))
        .when()
            .post("/api/products")
        .then()
            .statusCode(403);
    }

    @Test
    @Order(14)
    @Story("Create Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Analyst НЕ может создавать продукты (403)")
    void analystCannotCreateProduct() {
        authRequest(getAnalystToken())
            .body(Map.of("name", "Analyst Product", "quantity", 10, "price", 10.0))
        .when()
            .post("/api/products")
        .then()
            .statusCode(403);
    }

    @Test
    @Order(15)
    @Story("Create Product")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Создание продукта с пустым именем возвращает 400")
    void createProductWithEmptyName() {
        authRequest(getEmployeeToken())
            .body(Map.of("name", "", "quantity", 10, "price", 10.0))
        .when()
            .post("/api/products")
        .then()
            .statusCode(400);
    }

    @Test
    @Order(16)
    @Story("Create Product")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Создание продукта с отрицательным количеством возвращает 400")
    void createProductWithNegativeQuantity() {
        authRequest(getEmployeeToken())
            .body(Map.of("name", "Negative Qty", "quantity", -5, "price", 10.0))
        .when()
            .post("/api/products")
        .then()
            .statusCode(400);
    }

    @Test
    @Order(17)
    @Story("Create Product")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Создание продукта с отрицательной ценой возвращает 400")
    void createProductWithNegativePrice() {
        authRequest(getEmployeeToken())
            .body(Map.of("name", "Negative Price", "quantity", 10, "price", -99.99))
        .when()
            .post("/api/products")
        .then()
            .statusCode(400);
    }

    // ===========================================
    // GET PRODUCT BY ID
    // ===========================================

    @Test
    @Order(20)
    @Story("Get Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Получение продукта по ID")
    void getProductById() {
        Assumptions.assumeTrue(createdProductId != null, "Продукт не был создан");

        authRequest(getEmployeeToken())
        .when()
            .get("/api/products/" + createdProductId)
        .then()
            .statusCode(200)
            .body("id", equalTo(createdProductId))
            .body("name", equalTo(testProductName));
    }

    @Test
    @Order(21)
    @Story("Get Product")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Получение несуществующего продукта возвращает 404")
    void getProductByIdNotFound() {
        authRequest(getEmployeeToken())
        .when()
            .get("/api/products/999999")
        .then()
            .statusCode(404);
    }

    // ===========================================
    // UPDATE PRODUCT
    // ===========================================

    @Test
    @Order(30)
    @Story("Update Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Employee обновляет продукт успешно")
    void employeeUpdatesProduct() {
        Assumptions.assumeTrue(createdProductId != null, "Продукт не был создан");

        authRequest(getEmployeeToken())
            .body(Map.of(
                "name", testProductName + " Updated",
                "quantity", 200,
                "price", 59.99
            ))
        .when()
            .put("/api/products/" + createdProductId)
        .then()
            .statusCode(200)
            .body("quantity", equalTo(200))
            .body("price", equalTo(59.99F));
    }

    @Test
    @Order(31)
    @Story("Update Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Manager НЕ может обновлять продукты")
    void managerCannotUpdateProduct() {
        Assumptions.assumeTrue(createdProductId != null, "Продукт не был создан");

        authRequest(getManagerToken())
            .body(Map.of("name", "Hacked", "quantity", 999, "price", 0.01))
        .when()
            .put("/api/products/" + createdProductId)
        .then()
            .statusCode(403);
    }

    // ===========================================
    // DELETE PRODUCT
    // ===========================================

    @Test
    @Order(40)
    @Story("Delete Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Manager НЕ может удалять продукты")
    void managerCannotDeleteProduct() {
        Assumptions.assumeTrue(createdProductId != null, "Продукт не был создан");

        authRequest(getManagerToken())
        .when()
            .delete("/api/products/" + createdProductId)
        .then()
            .statusCode(403);
    }

    @Test
    @Order(41)
    @Story("Delete Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Admin НЕ может удалять продукты")
    void adminCannotDeleteProduct() {
        Assumptions.assumeTrue(createdProductId != null, "Продукт не был создан");

        authRequest(getAdminToken())
        .when()
            .delete("/api/products/" + createdProductId)
        .then()
            .statusCode(403);
    }

    @Test
    @Order(50)
    @Story("Delete Product")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Employee удаляет продукт успешно")
    void employeeDeletesProduct() {
        Assumptions.assumeTrue(createdProductId != null, "Продукт не был создан");

        authRequest(getEmployeeToken())
        .when()
            .delete("/api/products/" + createdProductId)
        .then()
            .statusCode(anyOf(is(200), is(204)));

        // Проверяем что продукт удалён
        authRequest(getEmployeeToken())
        .when()
            .get("/api/products/" + createdProductId)
        .then()
            .statusCode(404);
    }

    @Test
    @Order(51)
    @Story("Delete Product")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Удаление несуществующего продукта возвращает 404")
    void deleteNonExistentProduct() {
        authRequest(getEmployeeToken())
        .when()
            .delete("/api/products/999999")
        .then()
            .statusCode(404);
    }
}
