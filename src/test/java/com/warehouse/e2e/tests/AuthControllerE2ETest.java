package com.warehouse.e2e.tests;

import com.warehouse.e2e.base.BaseE2ETest;
import com.warehouse.e2e.data.TestData;
import com.warehouse.e2e.helpers.AuthHelper;
import io.qameta.allure.*;
import org.junit.jupiter.api.*;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;

/**
 * E2E тесты для AuthController.
 * Проверяет аутентификацию и авторизацию пользователей.
 */
@Epic("Warehouse API")
@Feature("Authentication")
@DisplayName("Auth Controller E2E Tests")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class AuthControllerE2ETest extends BaseE2ETest {

    private AuthHelper authHelper;

    @BeforeAll
    void setupHelpers() {
        authHelper = new AuthHelper(port);
    }

    @BeforeEach
    void clearCache() {
        AuthHelper.clearTokenCache();
    }

    // ==================== LOGIN TESTS ====================

    @Test
    @Order(1)
    @Story("User Login")
    @Severity(SeverityLevel.BLOCKER)
    @DisplayName("Успешный логин с корректными credentials")
    @Description("Проверяет успешную аутентификацию пользователя и получение JWT токена")
    void shouldLoginSuccessfully_whenCredentialsAreValid() {
        Allure.parameter("username", TestData.Users.SUPERUSER);

        var response = authHelper.login(
                TestData.Users.SUPERUSER,
                TestData.Users.SUPERUSER_PASSWORD
        );

        response.then()
                .statusCode(200)
                .body("token", notNullValue())
                .body("token", not(emptyString()))
                .body("username", equalTo(TestData.Users.SUPERUSER))
                .body("fullName", notNullValue())
                .body("role", equalTo("SUPER_USER"));

        String token = response.jsonPath().getString("token");
        assertThat(token)
                .as("JWT токен должен состоять из 3 частей")
                .contains(".")
                .matches("^[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+$");
    }

    @Test
    @Order(2)
    @Story("User Login")
    @Severity(SeverityLevel.BLOCKER)
    @DisplayName("Ошибка логина при неверном пароле")
    @Description("Проверяет что система отклоняет неверные credentials и возвращает 401")
    void shouldReturnUnauthorized_whenPasswordIsInvalid() {
        Allure.parameter("username", TestData.Users.ADMIN);
        Allure.parameter("password", "wrongpassword");

        var response = authHelper.login(
                TestData.Users.ADMIN,
                TestData.Users.INVALID_PASSWORD
        );

        response.then()
                .statusCode(401);
    }

    // ==================== CURRENT USER TESTS ====================

    @Test
    @Order(3)
    @Story("Current User Info")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Получение информации о текущем пользователе")
    @Description("Проверяет endpoint /api/auth/me с валидным токеном")
    void shouldReturnCurrentUser_whenTokenIsValid() {
        // Arrange
        String token = authHelper.getToken(
                TestData.Users.MANAGER,
                TestData.Users.MANAGER_PASSWORD
        );

        // Act
        var response = authHelper.getCurrentUser(token);

        // Assert
        response.then()
                .statusCode(200)
                .body("username", equalTo(TestData.Users.MANAGER))
                .body("role", equalTo("MANAGER"))
                .body("fullName", notNullValue());
    }

    @Test
    @Order(4)
    @Story("Current User Info")
    @Severity(SeverityLevel.CRITICAL)
    @DisplayName("Ошибка при невалидном токене")
    @Description("Проверяет что /api/auth/me возвращает 401 для невалидного токена")
    void shouldReturnUnauthorized_whenTokenIsInvalid() {
        var response = authHelper.getCurrentUser("invalid.token.here");

        response.then()
                .statusCode(401);
    }
}