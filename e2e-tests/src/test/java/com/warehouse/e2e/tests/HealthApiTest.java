package com.warehouse.e2e.tests;

import com.warehouse.e2e.base.BaseE2ETest;
import io.qameta.allure.*;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.hamcrest.Matchers.*;

/**
 * E2E тесты для Health и Actuator endpoints.
 * Проверяет доступность и работоспособность сервиса.
 */
@Epic("Warehouse API")
@Feature("Health & Monitoring")
@DisplayName("Health API Tests")
public class HealthApiTest extends BaseE2ETest {

    @Test
    @Story("Health Check")
    @Severity(SeverityLevel.BLOCKER)
    @DisplayName("Health endpoint возвращает UP")
    void healthEndpointReturnsUp() {
        request()
        .when()
            .get("/actuator/health")
        .then()
            .statusCode(200)
            .body("status", equalTo("UP"));
    }

    @Test
    @Story("Health Check")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Health endpoint доступен без авторизации")
    void healthEndpointIsPublic() {
        // Без токена должен работать
        request()
        .when()
            .get("/actuator/health")
        .then()
            .statusCode(200);
    }

    @Test
    @Story("Metrics")
    @Severity(SeverityLevel.NORMAL)
    @DisplayName("Prometheus метрики доступны")
    void prometheusMetricsAvailable() {
        request()
        .when()
            .get("/actuator/prometheus")
        .then()
            .statusCode(200)
            .contentType(containsString("text/plain"))
            .body(containsString("jvm_memory"));
    }

    @Test
    @Story("Info")
    @Severity(SeverityLevel.MINOR)
    @DisplayName("Info endpoint доступен")
    void infoEndpointAvailable() {
        request()
        .when()
            .get("/actuator/info")
        .then()
            .statusCode(200);
    }
}
