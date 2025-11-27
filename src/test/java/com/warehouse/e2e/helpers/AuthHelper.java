package com.warehouse.e2e.helpers;

import io.qameta.allure.Step;
import io.restassured.http.ContentType;
import io.restassured.response.Response;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import static io.restassured.RestAssured.given;

/**
 * Хелпер для работы с авторизацией в тестах.
 * Кэширует токены для повторного использования.
 */
public class AuthHelper {

    private static final Map<String, String> tokenCache = new ConcurrentHashMap<>();

    private final int port;

    public AuthHelper(int port) {
        this.port = port;
    }

    /**
     * Получает JWT токен для пользователя (с кэшированием)
     */
    @Step("Получение JWT токена для пользователя: {username}")
    public String getToken(String username, String password) {
        String cacheKey = username + ":" + port;

        return tokenCache.computeIfAbsent(cacheKey, k -> {
            Response response = given()
                    .port(port)
                    .contentType(ContentType.JSON)
                    .body(Map.of(
                            "username", username,
                            "password", password
                    ))
                    .when()
                    .post("/api/auth/login")
                    .then()
                    .statusCode(200)
                    .extract()
                    .response();

            return response.jsonPath().getString("token");
        });
    }

    /**
     * Выполняет логин и возвращает полный response
     */
    @Step("Логин пользователя: {username}")
    public Response login(String username, String password) {
        return given()
                .port(port)
                .contentType(ContentType.JSON)
                .body(Map.of(
                        "username", username,
                        "password", password
                ))
                .when()
                .post("/api/auth/login");
    }

    /**
     * Получает информацию о текущем пользователе
     */
    @Step("Получение информации о текущем пользователе")
    public Response getCurrentUser(String token) {
        return given()
                .port(port)
                .header("Authorization", "Bearer " + token)
                .when()
                .get("/api/auth/me");
    }

    /**
     * Очищает кэш токенов
     */
    public static void clearTokenCache() {
        tokenCache.clear();
    }
}