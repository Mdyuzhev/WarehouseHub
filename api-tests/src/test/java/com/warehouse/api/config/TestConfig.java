package com.warehouse.api.config;

import org.aeonbits.owner.Config;

@Config.Sources({
    "system:properties",
    "system:env",
    "classpath:test.properties"
})
public interface TestConfig extends Config {

    @Key("base.url")
    @DefaultValue("http://192.168.1.74:30080")
    String baseUrl();

    @Key("admin.username")
    @DefaultValue("admin")
    String adminUsername();

    @Key("admin.password")
    @DefaultValue("admin123")
    String adminPassword();

    @Key("manager.username")
    @DefaultValue("manager")
    String managerUsername();

    @Key("manager.password")
    @DefaultValue("manager123")
    String managerPassword();

    @Key("employee.username")
    @DefaultValue("employee")
    String employeeUsername();

    @Key("employee.password")
    @DefaultValue("employee123")
    String employeePassword();
}
