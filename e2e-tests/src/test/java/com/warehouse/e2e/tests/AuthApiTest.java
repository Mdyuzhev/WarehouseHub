package com.warehouse.e2e.tests;

import com.warehouse.e2e.base.BaseE2ETest;
import io.qameta.allure.*;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import java.util.Map;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

/**
 * E2E тесты для Authentication API.
 * Проверяет логин, токены, текущего пользователя.
 */
@Epic("Warehouse API")
@Feature("Authentication")
@DisplayName("Auth API Tests")
public class AuthApiTest extends BaseE2ETest {

    // ===========================================
    // LOGIN - Позитивные сценарии
    // ===========================================

    @Test
    @Story("Login")
    @Severity(SeverityLevel.BLOCKER)
    @DisplayName("Superuser успешно логинится")
    void superuserLoginSuccess() {
        request()
            .body(Map.of(
                "username", config.superuserUsername(),
                "password", config.superuserPassword()
            ))
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(200)
            .body("token", notNullValue())
            .body("token", startsWith("eyJ"))
            .body("username", equalTo(config.superuserUsername()))
            .body("role", equalTo("SUPER_USER"));
    }

    @ParameterizedTest(name = "Логин пользователя {0} с ролью {2}")
    @CsvSource({
        "admin, password123, ADMIN",
        "manager, password123, MANAGER",
        "employee, password123, EMPLOYEE",
        "analyst, password123, ANALYST"
    })
    @Story("Login")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Все роли успешно логинятся")
    void allRolesLoginSuccess(String username, String password, String expectedRole) {
        request()
            .body(Map.of("username", username, "password", password))
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(200)
            .body("token", notNullValue())
            .body("role", equalTo(expectedRole));
    }

    @Test
    @Story("Login")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Токен имеет правильный формат JWT")
    void tokenHasCorrectJwtFormat() {
        String token = request()
            .body(Map.of(
                "username", config.employeeUsername(),
                "password", config.employeePassword()
            ))
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(200)
            .extract()
            .path("token");

        // JWT токен должен иметь 3 части разделённые точками
        org.assertj.core.api.Assertions.assertThat(token)
            .as("JWT должен содержать 3 части")
            .matches("^[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+$");
    }

    // ===========================================
    // LOGIN - Негативные сценарии
    // ===========================================

    @Test
    @Story("Login")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Логин с неверным паролем возвращает 401")
    void loginWithWrongPassword() {
        request()
            .body(Map.of("username", "admin", "password", "wrongpassword"))
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(401);
    }

    @Test
    @Story("Login")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Логин с несуществующим пользователем возвращает 401")
    void loginWithNonExistentUser() {
        request()
            .body(Map.of("username", "nonexistent", "password", "password123"))
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(401);
    }

    @Test
    @Story("Login")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Логин с пустым username возвращает ошибку")
    void loginWithEmptyUsername() {
        request()
            .body(Map.of("username", "", "password", "password123"))
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(anyOf(is(400), is(401)));
    }

    @Test
    @Story("Login")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Логин с пустым паролем возвращает ошибку")
    void loginWithEmptyPassword() {
        request()
            .body(Map.of("username", "admin", "password", ""))
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(anyOf(is(400), is(401)));
    }

    @Test
    @Story("Login")
    @Severity(SeverityLevel.MINOR)
    @DisplayName("Логин без body возвращает 400")
    void loginWithoutBody() {
        request()
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(400);
    }

    // ===========================================
    // CURRENT USER (/api/auth/me)
    // ===========================================

    @Test
    @Story("Current User")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Получение текущего пользователя с валидным токеном")
    void getCurrentUserWithValidToken() {
        String token = getSuperuserToken();

        authRequest(token)
        .when()
            .get("/api/auth/me")
        .then()
            .statusCode(200)
            .body("username", equalTo(config.superuserUsername()))
            .body("role", equalTo("SUPER_USER"))
            .body("fullName", notNullValue());
    }

    @ParameterizedTest(name = "Текущий пользователь {0} имеет роль {1}")
    @CsvSource({
        "admin, ADMIN",
        "manager, MANAGER",
        "employee, EMPLOYEE",
        "analyst, ANALYST"
    })
    @Story("Current User")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Проверка роли для каждого пользователя")
    void getCurrentUserRoleVerification(String username, String expectedRole) {
        String token = getToken(username, "password123");

        authRequest(token)
        .when()
            .get("/api/auth/me")
        .then()
            .statusCode(200)
            .body("username", equalTo(username))
            .body("role", equalTo(expectedRole));
    }

    @Test
    @Story("Current User")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Запрос /me с невалидным токеном возвращает 401/403")
    void getCurrentUserWithInvalidToken() {
        authRequest("invalid.token.here")
        .when()
            .get("/api/auth/me")
        .then()
            .statusCode(anyOf(is(401), is(403)));
    }

    @Test
    @Story("Current User")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Запрос /me без токена возвращает 403")
    void getCurrentUserWithoutToken() {
        request()
        .when()
            .get("/api/auth/me")
        .then()
            .statusCode(403);
    }

    @Test
    @Story("Current User")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Запрос /me с malformed токеном возвращает ошибку")
    void getCurrentUserWithMalformedToken() {
        authRequest("not-a-jwt-token")
        .when()
            .get("/api/auth/me")
        .then()
            .statusCode(anyOf(is(401), is(403)));
    }
}
