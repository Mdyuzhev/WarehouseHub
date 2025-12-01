package com.warehouse.ui.tests;

import com.warehouse.ui.config.BaseTest;
import com.warehouse.ui.pages.AnalyticsPage;
import com.warehouse.ui.pages.LoginPage;
import io.qameta.allure.*;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

@Epic("Аналитика")
@Feature("Просмотр аналитики")
@Tag("analytics")
public class AnalyticsTest extends BaseTest {

    private final LoginPage loginPage = new LoginPage();
    private final AnalyticsPage analyticsPage = new AnalyticsPage();

    @Test
    @Story("Доступ к аналитике")
    @DisplayName("Аналитик может видеть раздел аналитики")
    @Description("Проверка что пользователь с ролью ANALYST имеет доступ к разделу аналитики")
    @Severity(SeverityLevel.CRITICAL)
    void testAnalystCanAccessAnalytics() {
        loginPage.login(config.analystUsername(), config.analystPassword());
        loginPage.verifyLoginSuccess();

        // Аналитик должен видеть навигацию к аналитике
        Assertions.assertTrue(analyticsPage.isAnalyticsNavVisible(),
            "Аналитик должен видеть ссылку на раздел 'Аналитика'");
    }

    @Test
    @Story("Доступ к аналитике")
    @DisplayName("Администратор может видеть раздел аналитики")
    @Description("Проверка что администратор имеет доступ к разделу аналитики")
    @Severity(SeverityLevel.NORMAL)
    void testAdminCanAccessAnalytics() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();

        // Админ тоже должен видеть аналитику
        Assertions.assertTrue(analyticsPage.isAnalyticsNavVisible(),
            "Администратор должен видеть ссылку на раздел 'Аналитика'");
    }
}
