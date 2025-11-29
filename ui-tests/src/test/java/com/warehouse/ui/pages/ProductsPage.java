package com.warehouse.ui.pages;

import com.codeborne.selenide.ElementsCollection;
import com.codeborne.selenide.SelenideElement;
import io.qameta.allure.Step;

import static com.codeborne.selenide.Condition.*;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.$$;

/**
 * Products Page Object for Warehouse application.
 */
public class ProductsPage {

    private final SelenideElement productsTable = $("table, .products-table, [class*='product-list']");
    private final ElementsCollection productRows = $$("table tbody tr, .product-row, [class*='product-item']");
    private final SelenideElement addProductButton = $("button:contains('Add'), .add-product-button, [class*='add-product']");
    private final SelenideElement searchInput = $("input[placeholder*='Search'], .search-input, [class*='search']");

    // Form fields
    private final SelenideElement nameInput = $("input[name='name'], #productName, [class*='name-input']");
    private final SelenideElement quantityInput = $("input[name='quantity'], #quantity, [class*='quantity-input']");
    private final SelenideElement priceInput = $("input[name='price'], #price, [class*='price-input']");
    private final SelenideElement categoryInput = $("input[name='category'], select[name='category'], #category");
    private final SelenideElement descriptionInput = $("textarea[name='description'], #description");
    private final SelenideElement saveButton = $("button[type='submit'], .save-button, button:contains('Save')");
    private final SelenideElement cancelButton = $(".cancel-button, button:contains('Cancel')");
    private final SelenideElement deleteButton = $(".delete-button, button:contains('Delete')");
    private final SelenideElement confirmDeleteButton = $(".confirm-delete, button:contains('Confirm')");

    @Step("Verify products table is visible")
    public ProductsPage verifyTableVisible() {
        productsTable.shouldBe(visible);
        return this;
    }

    @Step("Get products count")
    public int getProductsCount() {
        return productRows.size();
    }

    @Step("Click Add Product button")
    public ProductsPage clickAddProduct() {
        addProductButton.shouldBe(visible, enabled).click();
        return this;
    }

    @Step("Fill product form: {name}, qty={quantity}, price={price}")
    public ProductsPage fillProductForm(String name, int quantity, double price, String category, String description) {
        nameInput.shouldBe(visible).setValue(name);
        quantityInput.shouldBe(visible).setValue(String.valueOf(quantity));
        priceInput.shouldBe(visible).setValue(String.valueOf(price));
        if (category != null) {
            categoryInput.setValue(category);
        }
        if (description != null) {
            descriptionInput.setValue(description);
        }
        return this;
    }

    @Step("Save product")
    public ProductsPage saveProduct() {
        saveButton.shouldBe(visible, enabled).click();
        return this;
    }

    @Step("Create new product: {name}")
    public ProductsPage createProduct(String name, int quantity, double price, String category, String description) {
        clickAddProduct();
        fillProductForm(name, quantity, price, category, description);
        saveProduct();
        return this;
    }

    @Step("Search for product: {query}")
    public ProductsPage searchProduct(String query) {
        searchInput.shouldBe(visible).setValue(query);
        return this;
    }

    @Step("Verify product exists: {name}")
    public ProductsPage verifyProductExists(String name) {
        productsTable.shouldHave(text(name));
        return this;
    }

    @Step("Verify product does not exist: {name}")
    public ProductsPage verifyProductNotExists(String name) {
        productsTable.shouldNotHave(text(name));
        return this;
    }

    @Step("Click edit for product row {index}")
    public ProductsPage clickEditProduct(int index) {
        productRows.get(index).$(".edit-button, button:contains('Edit')").click();
        return this;
    }

    @Step("Click delete for product row {index}")
    public ProductsPage clickDeleteProduct(int index) {
        productRows.get(index).$(".delete-button, button:contains('Delete')").click();
        return this;
    }

    @Step("Confirm delete")
    public ProductsPage confirmDelete() {
        confirmDeleteButton.shouldBe(visible).click();
        return this;
    }
}
