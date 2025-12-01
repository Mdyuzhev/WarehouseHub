package com.warehouse.ui.pages;

import com.codeborne.selenide.ElementsCollection;
import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.$$;

/**
 * Page Object для страницы товаров системы Warehouse.
 * Использует data-testid атрибуты для надёжной идентификации элементов.
 */
public class ProductsPage {

    // Основные элементы раздела товаров
    private final SelenideElement productsSection = $("[data-testid='products-section']");
    private final SelenideElement productsTitle = $("[data-testid='products-title']");
    private final SelenideElement productsList = $("[data-testid='products-list']");
    private final ElementsCollection productItems = $$("[data-testid^='product-item-']");

    // Элементы навигации
    private final SelenideElement navAddProduct = $("[data-testid='nav-add-product']");
    // navProducts используется для навигации к списку товаров при необходимости
    @SuppressWarnings("unused")
    private final SelenideElement navProducts = $("[data-testid='nav-products']");

    @Step("Проверить отображение раздела 'Товары' на странице")
    public ProductsPage verifySectionVisible() {
        productsSection.shouldBe(visible);
        return this;
    }

    @Step("Проверить отображение заголовка раздела товаров")
    public ProductsPage verifyTitleVisible() {
        productsTitle.shouldBe(visible);
        return this;
    }

    @Step("Проверить отображение списка товаров на складе")
    public ProductsPage verifyListVisible() {
        productsList.shouldBe(visible);
        return this;
    }

    @Step("Получить количество товаров в списке")
    public int getProductsCount() {
        return productItems.size();
    }

    @Step("Проверить наличие хотя бы одного товара в списке")
    public ProductsPage verifyProductsExist() {
        productsList.shouldBe(visible);
        productItems.shouldHave(com.codeborne.selenide.CollectionCondition.sizeGreaterThan(0));
        return this;
    }

    @Step("Нажать кнопку 'Добавить товар' для перехода к форме создания")
    public ProductsPage clickAddProduct() {
        navAddProduct.shouldBe(visible, enabled).click();
        return this;
    }

    @Step("Нажать кнопку 'Редактировать' для товара с ID: {productId}")
    public ProductsPage clickEditProduct(int productId) {
        $("[data-testid='edit-product-" + productId + "']").shouldBe(visible, enabled).click();
        return this;
    }

    @Step("Нажать кнопку 'Удалить' для товара с ID: {productId}")
    public ProductsPage clickDeleteProduct(int productId) {
        $("[data-testid='delete-product-" + productId + "']").shouldBe(visible, enabled).click();
        return this;
    }

    @Step("Проверить видимость кнопки 'Редактировать' у товаров")
    public boolean isEditButtonVisible() {
        return $$("[data-testid^='edit-product-']").size() > 0;
    }

    @Step("Проверить видимость кнопки 'Удалить' у товаров")
    public boolean isDeleteButtonVisible() {
        return $$("[data-testid^='delete-product-']").size() > 0;
    }

    @Step("Проверить видимость кнопки 'Добавить товар' в навигации")
    public boolean isAddProductVisible() {
        return navAddProduct.isDisplayed();
    }
}
