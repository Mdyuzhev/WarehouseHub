package com.warehouse.api.tests;

import io.qameta.allure.*;
import io.restassured.RestAssured;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

@Epic("API")
@Feature("Authentication")
public class AuthApiTest extends BaseApiTest {

    @Test
    @Story("Login")
    @DisplayName("Admin should login successfully")
    @Severity(SeverityLevel.BLOCKER)
    void testAdminLogin() {
        given()
            .spec(spec)
            .body("{\"username\":\"" + config.adminUsername() + "\",\"password\":\"" + config.adminPassword() + "\"}")
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(200)
            .body("token", notNullValue())
            .body("token", startsWith("eyJ"));
    }

    @Test
    @Story("Login")
    @DisplayName("Manager should login successfully")
    @Severity(SeverityLevel.CRITICAL)
    void testManagerLogin() {
        given()
            .spec(spec)
            .body("{\"username\":\"" + config.managerUsername() + "\",\"password\":\"" + config.managerPassword() + "\"}")
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(200)
            .body("token", notNullValue());
    }

    @Test
    @Story("Login")
    @DisplayName("Employee should login successfully")
    @Severity(SeverityLevel.CRITICAL)
    void testEmployeeLogin() {
        given()
            .spec(spec)
            .body("{\"username\":\"" + config.employeeUsername() + "\",\"password\":\"" + config.employeePassword() + "\"}")
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(200)
            .body("token", notNullValue());
    }

    @Test
    @Story("Login")
    @DisplayName("Login should fail with wrong password")
    @Severity(SeverityLevel.CRITICAL)
    void testLoginWithWrongPassword() {
        given()
            .spec(spec)
            .body("{\"username\":\"admin\",\"password\":\"wrongpassword\"}")
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(anyOf(is(401), is(403)));
    }

    @Test
    @Story("Login")
    @DisplayName("Login should fail with non-existent user")
    @Severity(SeverityLevel.NORMAL)
    void testLoginWithNonExistentUser() {
        given()
            .spec(spec)
            .body("{\"username\":\"nonexistent\",\"password\":\"password123\"}")
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(anyOf(is(401), is(403)));
    }
}
