package com.warehouse.e2e.base;

import com.warehouse.e2e.config.TestConfig;
import io.qameta.allure.restassured.AllureRestAssured;
import io.restassured.RestAssured;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.filter.log.LogDetail;
import io.restassured.http.ContentType;
import io.restassured.specification.RequestSpecification;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.TestInstance;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import static io.restassured.RestAssured.given;

/**
 * Базовый класс для всех E2E тестов.
 * Предоставляет общую конфигурацию RestAssured и методы авторизации.
 */
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
public abstract class BaseE2ETest {

    protected static TestConfig config;
    protected static RequestSpecification spec;

    // Кэш токенов для переиспользования
    private static final Map<String, String> tokenCache = new ConcurrentHashMap<>();

    @BeforeAll
    static void setupRestAssured() {
        config = TestConfig.getInstance();

        RestAssured.baseURI = config.baseUrl();
        RestAssured.enableLoggingOfRequestAndResponseIfValidationFails(LogDetail.ALL);

        spec = new RequestSpecBuilder()
                .setBaseUri(config.baseUrl())
                .setContentType(ContentType.JSON)
                .setAccept(ContentType.JSON)
                .addFilter(new AllureRestAssured())
                .log(LogDetail.URI)
                .log(LogDetail.METHOD)
                .build();
    }

    @BeforeEach
    void beforeEach() {
        // Можно добавить очистку между тестами если нужно
    }

    // ===========================================
    // Методы авторизации
    // ===========================================

    /**
     * Получает JWT токен для пользователя (с кэшированием)
     */
    protected static String getToken(String username, String password) {
        String cacheKey = username + "@" + config.baseUrl();

        return tokenCache.computeIfAbsent(cacheKey, k -> {
            return given()
                    .spec(spec)
                    .body(Map.of("username", username, "password", password))
                    .when()
                    .post("/api/auth/login")
                    .then()
                    .statusCode(200)
                    .extract()
                    .path("token");
        });
    }

    protected static String getSuperuserToken() {
        return getToken(config.superuserUsername(), config.superuserPassword());
    }

    protected static String getAdminToken() {
        return getToken(config.adminUsername(), config.adminPassword());
    }

    protected static String getManagerToken() {
        return getToken(config.managerUsername(), config.managerPassword());
    }

    protected static String getEmployeeToken() {
        return getToken(config.employeeUsername(), config.employeePassword());
    }

    protected static String getAnalystToken() {
        return getToken(config.analystUsername(), config.analystPassword());
    }

    /**
     * Очищает кэш токенов
     */
    protected static void clearTokenCache() {
        tokenCache.clear();
    }

    // ===========================================
    // Вспомогательные методы
    // ===========================================

    /**
     * Создаёт авторизованный запрос с токеном
     */
    protected RequestSpecification authRequest(String token) {
        return given()
                .spec(spec)
                .header("Authorization", "Bearer " + token);
    }

    /**
     * Создаёт неавторизованный запрос
     */
    protected RequestSpecification request() {
        return given().spec(spec);
    }
}
