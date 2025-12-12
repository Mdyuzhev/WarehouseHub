package com.warehouse.ui.tests;

import com.warehouse.ui.config.BaseTest;
import com.warehouse.ui.pages.LoginPage;
import io.qameta.allure.*;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

@Epic("Аутентификация")
@Feature("Вход в систему")
@Tag("login")
public class LoginTest extends BaseTest {

    private final LoginPage loginPage = new LoginPage();

    @Test
    @Story("Успешный вход")
    @DisplayName("Администратор может войти в систему с корректными учётными данными")
    @Description("Проверка входа администратора (роль ADMIN) в систему управления складом")
    @Severity(SeverityLevel.BLOCKER)
    void testAdminLogin() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();
    }

    @Test
    @Story("Успешный вход")
    @DisplayName("Менеджер может войти в систему с корректными учётными данными")
    @Description("Проверка входа менеджера (роль MANAGER) в систему управления складом")
    @Severity(SeverityLevel.CRITICAL)
    void testManagerLogin() {
        loginPage.login(config.managerUsername(), config.managerPassword());
        loginPage.verifyLoginSuccess();
    }

    @Test
    @Story("Успешный вход")
    @DisplayName("Сотрудник может войти в систему с корректными учётными данными")
    @Description("Проверка входа сотрудника (роль EMPLOYEE) в систему управления складом")
    @Severity(SeverityLevel.CRITICAL)
    void testEmployeeLogin() {
        loginPage.login(config.employeeUsername(), config.employeePassword());
        loginPage.verifyLoginSuccess();
    }

    @Test
    @Story("Неуспешный вход")
    @DisplayName("Вход с неверным паролем должен быть отклонён")
    @Description("Система должна отображать сообщение об ошибке при попытке входа с неверным паролем")
    @Severity(SeverityLevel.CRITICAL)
    void testInvalidPassword() {
        loginPage.login(config.adminUsername(), "wrongpassword");
        loginPage.verifyErrorDisplayed();
    }

    @Test
    @Story("Неуспешный вход")
    @DisplayName("Вход с несуществующим пользователем должен быть отклонён")
    @Description("Система должна отображать сообщение об ошибке при попытке входа с несуществующим логином")
    @Severity(SeverityLevel.NORMAL)
    void testNonExistentUser() {
        loginPage.login("nonexistent", "password123");
        loginPage.verifyErrorDisplayed();
    }

    @Test
    @Story("Выход из системы")
    @DisplayName("Пользователь может выйти из системы")
    @Description("После нажатия кнопки выхода пользователь должен быть перенаправлен на страницу входа")
    @Severity(SeverityLevel.CRITICAL)
    void testLogout() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();
        loginPage.logout();
        // После выхода форма входа должна быть доступна снова
        loginPage.enterUsername("");
    }
}
