package com.warehouse.ui.config;

import org.aeonbits.owner.Config;

/**
 * Конфигурация UI тестов.
 * WH-175: Credentials можно переопределить через:
 * 1. test.properties (см. test.properties.example)
 * 2. Системные переменные окружения
 * 3. -D параметры JVM
 */
@Config.Sources({
        "classpath:test.properties",
        "system:env"
})
public interface TestConfig extends Config {

    @Key("base.url")
    @DefaultValue("http://192.168.1.74:30081")
    String baseUrl();

    @Key("selenoid.url")
    @DefaultValue("http://192.168.1.74:4444/wd/hub")
    String selenoidUrl();

    @Key("browser")
    @DefaultValue("chrome")
    String browser();

    @Key("browser.size")
    @DefaultValue("1920x1080")
    String browserSize();

    @Key("timeout")
    @DefaultValue("10000")
    int timeout();

    @Key("headless")
    @DefaultValue("true")
    boolean headless();

    @Key("test.user.admin")
    @DefaultValue("admin")
    String adminUsername();

    @Key("test.user.admin.password")
    @DefaultValue("admin123")
    String adminPassword();

    @Key("test.user.manager")
    @DefaultValue("admin")
    String managerUsername();

    @Key("test.user.manager.password")
    @DefaultValue("admin123")
    String managerPassword();

    @Key("test.user.employee")
    @DefaultValue("wh_north_op")
    String employeeUsername();

    @Key("test.user.employee.password")
    @DefaultValue("password123")
    String employeePassword();

    @Key("test.user.analyst")
    @DefaultValue("admin")
    String analystUsername();

    @Key("test.user.analyst.password")
    @DefaultValue("admin123")
    String analystPassword();
}
