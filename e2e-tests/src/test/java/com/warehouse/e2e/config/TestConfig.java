package com.warehouse.e2e.config;

import org.aeonbits.owner.Config;
import org.aeonbits.owner.ConfigFactory;

/**
 * Конфигурация E2E тестов.
 * WH-176: Credentials можно переопределить через:
 * 1. test.properties (см. test.properties.example)
 * 2. Системные переменные окружения
 * 3. -D параметры JVM (system:properties)
 */
@Config.Sources({
    "system:properties",
    "system:env",
    "classpath:test.properties"
})
public interface TestConfig extends Config {

    @Key("base.url")
    @DefaultValue("http://192.168.1.74:30080")
    String baseUrl();

    // Пользователи (пароль для всех: password123)
    @Key("superuser.username")
    @DefaultValue("superuser")
    String superuserUsername();

    @Key("superuser.password")
    @DefaultValue("password123")
    String superuserPassword();

    @Key("admin.username")
    @DefaultValue("admin")
    String adminUsername();

    @Key("admin.password")
    @DefaultValue("password123")
    String adminPassword();

    @Key("manager.username")
    @DefaultValue("manager")
    String managerUsername();

    @Key("manager.password")
    @DefaultValue("password123")
    String managerPassword();

    @Key("employee.username")
    @DefaultValue("employee")
    String employeeUsername();

    @Key("employee.password")
    @DefaultValue("password123")
    String employeePassword();

    @Key("analyst.username")
    @DefaultValue("analyst")
    String analystUsername();

    @Key("analyst.password")
    @DefaultValue("password123")
    String analystPassword();

    static TestConfig getInstance() {
        return ConfigFactory.create(TestConfig.class, System.getProperties(), System.getenv());
    }
}
