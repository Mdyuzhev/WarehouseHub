package com.warehouse.ui.config;

import com.codeborne.selenide.Configuration;
import com.codeborne.selenide.logevents.SelenideLogger;
import io.qameta.allure.selenide.AllureSelenide;
import org.aeonbits.owner.ConfigFactory;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;

import static com.codeborne.selenide.Selenide.closeWebDriver;
import static com.codeborne.selenide.Selenide.open;

public abstract class BaseTest {

    protected static TestConfig config = ConfigFactory.create(TestConfig.class, System.getenv());

    @BeforeAll
    static void setupAll() {
        Configuration.browser = config.browser();
        Configuration.browserSize = config.browserSize();
        Configuration.timeout = config.timeout();
        Configuration.headless = config.headless();
        Configuration.baseUrl = config.baseUrl();

        // Selenoid remote
        String selenoidUrl = config.selenoidUrl();
        if (selenoidUrl != null && !selenoidUrl.isEmpty()) {
            Configuration.remote = selenoidUrl;
        }

        // Allure integration
        SelenideLogger.addListener("AllureSelenide", new AllureSelenide()
                .screenshots(true)
                .savePageSource(true));
    }

    @BeforeEach
    void setup() {
        open("/");
    }

    @AfterEach
    void tearDown() {
        closeWebDriver();
    }
}
