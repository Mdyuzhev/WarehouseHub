package com.warehouse.ui.tests;

import com.warehouse.ui.config.BaseTest;
import com.warehouse.ui.config.Selectors;
import com.warehouse.ui.pages.LoginPage;
import com.warehouse.ui.pages.ProductsPage;
import io.qameta.allure.*;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;

@Epic("Авторизация")
@Feature("Ролевая модель доступа (RBAC)")
@Tag("rbac")
public class RoleAccessTest extends BaseTest {

    private final LoginPage loginPage = new LoginPage();
    private final ProductsPage productsPage = new ProductsPage();

    @Test
    @Story("Доступ администратора")
    @DisplayName("Администратор имеет полный доступ к управлению товарами")
    @Description("Проверка что администратор (роль ADMIN) видит все кнопки управления: добавление, редактирование и удаление товаров")
    @Severity(SeverityLevel.CRITICAL)
    void testAdminFullAccess() {
        loginPage.login(config.adminUsername(), config.adminPassword());
        loginPage.verifyLoginSuccess();

        // Администратор должен видеть раздел товаров
        productsPage.verifySectionVisible();

        // Администратор должен видеть кнопку добавления товара
        Assertions.assertTrue(productsPage.isAddProductVisible(), "Администратор должен видеть кнопку 'Добавить товар'");

        // Администратор должен видеть кнопки редактирования
        Assertions.assertTrue(productsPage.isEditButtonVisible(), "Администратор должен видеть кнопки 'Редактировать'");

        // Администратор должен видеть кнопки удаления
        Assertions.assertTrue(productsPage.isDeleteButtonVisible(), "Администратор должен видеть кнопки 'Удалить'");
    }

    @Test
    @Story("Доступ менеджера")
    @DisplayName("Менеджер может просматривать и редактировать товары")
    @Description("Проверка что менеджер (роль MANAGER) имеет доступ к просмотру, добавлению и редактированию товаров")
    @Severity(SeverityLevel.CRITICAL)
    void testManagerAccess() {
        loginPage.login(config.managerUsername(), config.managerPassword());
        loginPage.verifyLoginSuccess();

        // Менеджер должен видеть раздел товаров
        productsPage.verifySectionVisible();

        // Менеджер должен видеть кнопку добавления товара
        Assertions.assertTrue(productsPage.isAddProductVisible(), "Менеджер должен видеть кнопку 'Добавить товар'");

        // Менеджер должен видеть кнопки редактирования
        Assertions.assertTrue(productsPage.isEditButtonVisible(), "Менеджер должен видеть кнопки 'Редактировать'");
    }

    @Test
    @Story("Доступ сотрудника")
    @DisplayName("Сотрудник имеет только права на просмотр товаров")
    @Description("Проверка что сотрудник (роль EMPLOYEE) не видит кнопки управления товарами - только просмотр списка")
    @Severity(SeverityLevel.CRITICAL)
    void testEmployeeReadOnly() {
        loginPage.login(config.employeeUsername(), config.employeePassword());
        loginPage.verifyLoginSuccess();

        // Сотрудник должен видеть раздел товаров
        productsPage.verifySectionVisible();

        // Сотрудник НЕ должен видеть кнопку добавления товара
        Assertions.assertFalse(productsPage.isAddProductVisible(), "Сотрудник НЕ должен видеть кнопку 'Добавить товар'");

        // Сотрудник НЕ должен видеть кнопки редактирования
        Assertions.assertFalse(productsPage.isEditButtonVisible(), "Сотрудник НЕ должен видеть кнопки 'Редактировать'");

        // Сотрудник НЕ должен видеть кнопки удаления
        Assertions.assertFalse(productsPage.isDeleteButtonVisible(), "Сотрудник НЕ должен видеть кнопки 'Удалить'");
    }

    @Test
    @Story("Неавторизованный доступ")
    @DisplayName("Неавторизованный пользователь видит страницу входа")
    @Description("Проверка редиректа неавторизованного пользователя на страницу входа при попытке доступа к системе")
    @Severity(SeverityLevel.BLOCKER)
    void testUnauthenticatedRedirect() {
        // При открытии приложения без авторизации
        // Должна отображаться форма входа (редирект на страницу логина)
        Selectors.waitForLoginForm();
        Selectors.password().shouldBe(visible, Selectors.PAGE_LOAD_TIMEOUT);
        Selectors.loginButton().shouldBe(visible, Selectors.PAGE_LOAD_TIMEOUT);
    }
}
