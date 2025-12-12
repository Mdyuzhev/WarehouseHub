package com.warehouse.ui.config;

import com.codeborne.selenide.Configuration;
import com.codeborne.selenide.Selenide;
import com.codeborne.selenide.logevents.SelenideLogger;
import io.qameta.allure.Attachment;
import io.qameta.allure.selenide.AllureSelenide;
import org.aeonbits.owner.ConfigFactory;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.remote.DesiredCapabilities;

import static com.codeborne.selenide.Selenide.closeWebDriver;
import static com.codeborne.selenide.Selenide.open;

@SuppressWarnings("null")
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

            // Selenoid capabilities for VNC (video disabled for stability)
            DesiredCapabilities capabilities = new DesiredCapabilities();
            capabilities.setCapability("selenoid:options", new java.util.HashMap<String, Object>() {{
                put("enableVNC", true);
                put("enableVideo", false);
            }});
            Configuration.browserCapabilities = capabilities;
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
        takeScreenshot();
        closeWebDriver();
    }

    @Attachment(value = "Screenshot", type = "image/png")
    public byte[] takeScreenshot() {
        return Selenide.screenshot(OutputType.BYTES);
    }
}
