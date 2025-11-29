package com.warehouse.ui.pages;

import com.codeborne.selenide.ElementsCollection;
import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.$$;

/**
 * Products Page Object for Warehouse application.
 * Uses data-testid attributes for reliable element selection.
 */
public class ProductsPage {

    // Main elements
    private final SelenideElement productsSection = $("[data-testid='products-section']");
    private final SelenideElement productsTitle = $("[data-testid='products-title']");
    private final SelenideElement productsList = $("[data-testid='products-list']");
    private final ElementsCollection productItems = $$("[data-testid^='product-item-']");

    // Navigation
    private final SelenideElement navAddProduct = $("[data-testid='nav-add-product']");
    private final SelenideElement navProducts = $("[data-testid='nav-products']");

    @Step("Verify products section is visible")
    public ProductsPage verifySectionVisible() {
        productsSection.shouldBe(visible);
        return this;
    }

    @Step("Verify products title is visible")
    public ProductsPage verifyTitleVisible() {
        productsTitle.shouldBe(visible);
        return this;
    }

    @Step("Verify products list is visible")
    public ProductsPage verifyListVisible() {
        productsList.shouldBe(visible);
        return this;
    }

    @Step("Get products count")
    public int getProductsCount() {
        return productItems.size();
    }

    @Step("Verify at least one product exists")
    public ProductsPage verifyProductsExist() {
        productsList.shouldBe(visible);
        productItems.shouldHave(com.codeborne.selenide.CollectionCondition.sizeGreaterThan(0));
        return this;
    }

    @Step("Navigate to Add Product page")
    public ProductsPage clickAddProduct() {
        navAddProduct.shouldBe(visible, enabled).click();
        return this;
    }

    @Step("Click edit button for product with id {productId}")
    public ProductsPage clickEditProduct(int productId) {
        $("[data-testid='edit-product-" + productId + "']").shouldBe(visible, enabled).click();
        return this;
    }

    @Step("Click delete button for product with id {productId}")
    public ProductsPage clickDeleteProduct(int productId) {
        $("[data-testid='delete-product-" + productId + "']").shouldBe(visible, enabled).click();
        return this;
    }

    @Step("Verify edit button is visible for any product")
    public boolean isEditButtonVisible() {
        return $$("[data-testid^='edit-product-']").size() > 0;
    }

    @Step("Verify delete button is visible for any product")
    public boolean isDeleteButtonVisible() {
        return $$("[data-testid^='delete-product-']").size() > 0;
    }

    @Step("Verify Add Product navigation is visible")
    public boolean isAddProductVisible() {
        return navAddProduct.isDisplayed();
    }
}
