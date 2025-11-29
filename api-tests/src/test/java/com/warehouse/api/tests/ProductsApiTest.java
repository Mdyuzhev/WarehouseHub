package com.warehouse.api.tests;

import io.qameta.allure.*;
import org.junit.jupiter.api.*;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

@Epic("API")
@Feature("Products Management")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ProductsApiTest extends BaseApiTest {

    private static String employeeToken;
    private static String adminToken;
    private static Integer createdProductId;

    @BeforeAll
    static void setup() {
        employeeToken = getEmployeeToken();
        adminToken = getAdminToken();
    }

    @Test
    @Order(1)
    @Story("Get Products")
    @DisplayName("Should get list of products")
    @Severity(SeverityLevel.BLOCKER)
    void testGetProducts() {
        given()
            .spec(spec)
            .header("Authorization", "Bearer " + employeeToken)
        .when()
            .get("/api/products")
        .then()
            .statusCode(200)
            .body("$", instanceOf(java.util.List.class));
    }

    @Test
    @Order(2)
    @Story("Create Product")
    @DisplayName("Employee should create product successfully")
    @Severity(SeverityLevel.BLOCKER)
    void testCreateProduct() {
        String productName = "API Test Product " + System.currentTimeMillis();

        createdProductId = given()
            .spec(spec)
            .header("Authorization", "Bearer " + employeeToken)
            .body("{\"name\":\"" + productName + "\",\"quantity\":100,\"price\":99.99}")
        .when()
            .post("/api/products")
        .then()
            .statusCode(201)
            .body("id", notNullValue())
            .body("name", equalTo(productName))
            .body("quantity", equalTo(100))
            .extract()
            .path("id");
    }

    @Test
    @Order(3)
    @Story("Get Product")
    @DisplayName("Should get product by ID")
    @Severity(SeverityLevel.CRITICAL)
    void testGetProductById() {
        Assumptions.assumeTrue(createdProductId != null, "Product was not created");

        given()
            .spec(spec)
            .header("Authorization", "Bearer " + employeeToken)
        .when()
            .get("/api/products/" + createdProductId)
        .then()
            .statusCode(200)
            .body("id", equalTo(createdProductId));
    }

    @Test
    @Order(4)
    @Story("Update Product")
    @DisplayName("Should update product")
    @Severity(SeverityLevel.CRITICAL)
    void testUpdateProduct() {
        Assumptions.assumeTrue(createdProductId != null, "Product was not created");

        given()
            .spec(spec)
            .header("Authorization", "Bearer " + employeeToken)
            .body("{\"name\":\"Updated Product\",\"quantity\":200,\"price\":149.99}")
        .when()
            .put("/api/products/" + createdProductId)
        .then()
            .statusCode(200)
            .body("quantity", equalTo(200))
            .body("price", equalTo(149.99F));
    }

    @Test
    @Order(5)
    @Story("Delete Product")
    @DisplayName("Admin should delete product")
    @Severity(SeverityLevel.CRITICAL)
    void testDeleteProduct() {
        Assumptions.assumeTrue(createdProductId != null, "Product was not created");

        given()
            .spec(spec)
            .header("Authorization", "Bearer " + adminToken)
        .when()
            .delete("/api/products/" + createdProductId)
        .then()
            .statusCode(anyOf(is(200), is(204)));
    }

    @Test
    @Order(10)
    @Story("Security")
    @DisplayName("Should return 403 without token")
    @Severity(SeverityLevel.CRITICAL)
    void testUnauthorizedAccess() {
        given()
            .spec(spec)
            // No Authorization header
        .when()
            .get("/api/products")
        .then()
            .statusCode(403);
    }

    @Test
    @Order(11)
    @Story("Security")
    @DisplayName("Should return 403 with invalid token")
    @Severity(SeverityLevel.CRITICAL)
    void testInvalidToken() {
        given()
            .spec(spec)
            .header("Authorization", "Bearer invalid.token.here")
        .when()
            .get("/api/products")
        .then()
            .statusCode(403);
    }
}
