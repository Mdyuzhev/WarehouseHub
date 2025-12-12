package com.warehouse.e2e.config;

import org.aeonbits.owner.Config;
import org.aeonbits.owner.ConfigFactory;

/**
 * Конфигурация E2E тестов.
 * WH-176: Credentials можно переопределить через:
 * 1. -D параметры JVM (system:properties)
 * 2. Системные переменные окружения
 * 3. test.properties (см. test.properties.example)
 *
 * DefaultValues соответствуют dev окружению (31080) и реальным пользователям.
 */
@Config.Sources({
    "system:properties",
    "system:env",
    "classpath:test.properties"
})
public interface TestConfig extends Config {

    @Key("base.url")
    @DefaultValue("http://192.168.1.74:31080")
    String baseUrl();

    // Superuser = admin (ROLE_SUPER_USER)
    @Key("superuser.username")
    @DefaultValue("admin")
    String superuserUsername();

    @Key("superuser.password")
    @DefaultValue("admin123")
    String superuserPassword();

    // Admin = admin (ROLE_SUPER_USER)
    @Key("admin.username")
    @DefaultValue("admin")
    String adminUsername();

    @Key("admin.password")
    @DefaultValue("admin123")
    String adminPassword();

    // Manager = admin (SUPER_USER имеет все права, нет отдельного MANAGER)
    @Key("manager.username")
    @DefaultValue("admin")
    String managerUsername();

    @Key("manager.password")
    @DefaultValue("admin123")
    String managerPassword();

    // Employee = wh_north_op (ROLE_EMPLOYEE, facility WH-C-001)
    @Key("employee.username")
    @DefaultValue("wh_north_op")
    String employeeUsername();

    @Key("employee.password")
    @DefaultValue("password123")
    String employeePassword();

    // Analyst = pp_1_op (ROLE_EMPLOYEE, facility PP-C-001)
    @Key("analyst.username")
    @DefaultValue("pp_1_op")
    String analystUsername();

    @Key("analyst.password")
    @DefaultValue("password123")
    String analystPassword();

    static TestConfig getInstance() {
        return ConfigFactory.create(TestConfig.class, System.getProperties(), System.getenv());
    }
}
