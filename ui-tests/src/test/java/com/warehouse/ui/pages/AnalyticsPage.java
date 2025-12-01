package com.warehouse.ui.pages;

import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;

/**
 * Page Object для страницы аналитики системы Warehouse.
 * Использует data-testid атрибуты для надёжной идентификации элементов.
 */
public class AnalyticsPage {

    // Элементы навигации
    private final SelenideElement navAnalytics = $("[data-testid='nav-analytics']");

    // Элементы страницы аналитики
    private final SelenideElement analyticsSection = $("[data-testid='analytics-section']");
    private final SelenideElement analyticsTitle = $("[data-testid='analytics-title']");
    private final SelenideElement analyticsChart = $("[data-testid='analytics-chart']");

    @Step("Перейти в раздел 'Аналитика'")
    public AnalyticsPage navigateToAnalytics() {
        navAnalytics.shouldBe(visible, enabled).click();
        return this;
    }

    @Step("Проверить отображение раздела 'Аналитика'")
    public AnalyticsPage verifySectionVisible() {
        analyticsSection.shouldBe(visible);
        return this;
    }

    @Step("Проверить отображение заголовка 'Аналитика'")
    public AnalyticsPage verifyTitleVisible() {
        analyticsTitle.shouldBe(visible);
        return this;
    }

    @Step("Проверить отображение графика аналитики")
    public AnalyticsPage verifyChartVisible() {
        analyticsChart.shouldBe(visible);
        return this;
    }

    @Step("Проверить видимость навигации 'Аналитика'")
    public boolean isAnalyticsNavVisible() {
        return navAnalytics.isDisplayed();
    }
}
