package com.warehouse.api.tests;

import com.warehouse.api.config.TestConfig;
import io.qameta.allure.restassured.AllureRestAssured;
import io.restassured.RestAssured;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.filter.log.LogDetail;
import io.restassured.http.ContentType;
import io.restassured.specification.RequestSpecification;
import org.aeonbits.owner.ConfigFactory;
import org.junit.jupiter.api.BeforeAll;

public abstract class BaseApiTest {

    protected static TestConfig config;
    protected static RequestSpecification spec;

    @BeforeAll
    static void setupAll() {
        config = ConfigFactory.create(TestConfig.class, System.getProperties(), System.getenv());

        RestAssured.baseURI = config.baseUrl();

        spec = new RequestSpecBuilder()
                .setContentType(ContentType.JSON)
                .setAccept(ContentType.JSON)
                .addFilter(new AllureRestAssured())
                .log(LogDetail.ALL)
                .build();
    }

    /**
     * Get JWT token for authentication
     */
    protected static String getToken(String username, String password) {
        return RestAssured.given()
                .spec(spec)
                .body("{\"username\":\"" + username + "\",\"password\":\"" + password + "\"}")
                .when()
                .post("/api/auth/login")
                .then()
                .statusCode(200)
                .extract()
                .path("token");
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
}
