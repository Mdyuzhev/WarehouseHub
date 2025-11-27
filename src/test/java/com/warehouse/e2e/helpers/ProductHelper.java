package com.warehouse.e2e.helpers;

import io.qameta.allure.Step;
import io.restassured.http.ContentType;
import io.restassured.response.Response;

import java.util.Map;

import static io.restassured.RestAssured.given;

/**
 * Хелпер для работы с API продуктов в тестах.
 */
public class ProductHelper {

    private final int port;
    private final AuthHelper authHelper;

    public ProductHelper(int port, AuthHelper authHelper) {
        this.port = port;
        this.authHelper = authHelper;
    }

    /**
     * Получает список всех продуктов
     */
    @Step("Получение списка всех продуктов")
    public Response getAllProducts(String token) {
        return given()
                .port(port)
                .header("Authorization", "Bearer " + token)
                .when()
                .get("/api/products");
    }

    /**
     * Создаёт новый продукт
     */
    @Step("Создание продукта: {name}, количество: {quantity}, цена: {price}")
    public Response createProduct(String token, String name, int quantity, double price) {
        return given()
                .port(port)
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + token)
                .body(Map.of(
                        "name", name,
                        "quantity", quantity,
                        "price", price
                ))
                .when()
                .post("/api/products");
    }

    /**
     * Удаляет продукт по ID
     */
    @Step("Удаление продукта с ID: {productId}")
    public Response deleteProduct(String token, Long productId) {
        return given()
                .port(port)
                .header("Authorization", "Bearer " + token)
                .when()
                .delete("/api/products/" + productId);
    }

    /**
     * Создаёт тестовый продукт и возвращает его ID
     */
    @Step("Создание тестового продукта для теста")
    public Long createTestProduct(String token) {
        Response response = createProduct(token,
                "Test Product " + System.currentTimeMillis(),
                10,
                99.99);

        if (response.statusCode() == 201 || response.statusCode() == 200) {
            return response.jsonPath().getLong("id");
        }
        throw new RuntimeException("Failed to create test product: " + response.asString());
    }
}