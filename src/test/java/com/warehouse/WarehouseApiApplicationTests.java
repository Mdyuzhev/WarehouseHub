package com.warehouse;

import io.qameta.allure.*;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("test")
@Epic("API")
@Feature("Application Startup")
class WarehouseApiApplicationTests {

    @Test
    @Story("Context Loading")
    @DisplayName("Spring context should load successfully")
    @Severity(SeverityLevel.BLOCKER)
    void contextLoads() {
    }
}