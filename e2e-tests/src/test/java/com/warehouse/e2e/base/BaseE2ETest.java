package com.warehouse.e2e.base;

import io.qameta.allure.restassured.AllureRestAssured;
import io.restassured.RestAssured;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.builder.ResponseSpecBuilder;
import io.restassured.filter.log.LogDetail;
import io.restassured.http.ContentType;
import io.restassured.specification.RequestSpecification;
import io.restassured.specification.ResponseSpecification;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.TestInstance;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.ActiveProfiles;

import static io.restassured.RestAssured.given;

/**
 * Базовый класс для всех E2E тестов.
 * Предоставляет общую конфигурацию RestAssured и вспомогательные методы.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
public abstract class BaseE2ETest {

    @LocalServerPort
    protected int port;

    protected static RequestSpecification baseRequestSpec;
    protected static ResponseSpecification successResponseSpec;
    protected static ResponseSpecification errorResponseSpec;

    // Тестовые пользователи
    protected static final String SUPERUSER = "superuser";
    protected static final String SUPERUSER_PASSWORD = "super123";
    protected static final String ADMIN = "admin";
    protected static final String ADMIN_PASSWORD = "admin123";
    protected static final String MANAGER = "manager";
    protected static final String MANAGER_PASSWORD = "manager123";
    protected static final String EMPLOYEE = "employee";
    protected static final String EMPLOYEE_PASSWORD = "employee123";

    @BeforeAll
    void setupRestAssured() {
        RestAssured.port = port;
        RestAssured.enableLoggingOfRequestAndResponseIfValidationFails(LogDetail.ALL);

        // Базовая спецификация запроса
        baseRequestSpec = new RequestSpecBuilder()
                .setContentType(ContentType.JSON)
                .setAccept(ContentType.JSON)
                .addFilter(new AllureRestAssured())
                .log(LogDetail.URI)
                .log(LogDetail.METHOD)
                .build();

        // Спецификация успешного ответа
        successResponseSpec = new ResponseSpecBuilder()
                .expectContentType(ContentType.JSON)
                .log(LogDetail.STATUS)
                .build();

        // Спецификация ошибки
        errorResponseSpec = new ResponseSpecBuilder()
                .log(LogDetail.ALL)
                .build();
    }

    @BeforeEach
    void resetRestAssured() {
        RestAssured.reset();
        RestAssured.port = port;
    }

    /**
     * Создаёт запрос с базовыми настройками
     */
    protected RequestSpecification request() {
        return given()
                .spec(baseRequestSpec)
                .port(port);
    }

    /**
     * Создаёт запрос с JWT токеном
     */
    protected RequestSpecification authenticatedRequest(String token) {
        return request()
                .header("Authorization", "Bearer " + token);
    }
}