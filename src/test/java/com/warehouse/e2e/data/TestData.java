package com.warehouse.e2e.data;

import io.qameta.allure.Allure;

import java.util.UUID;

/**
 * Тестовые данные и утилиты для генерации данных.
 */
public final class TestData {

    private TestData() {
        // Utility class
    }

    // ==================== USERS ====================

    public static class Users {
        public static final String SUPERUSER = "superuser";
        public static final String SUPERUSER_PASSWORD = "super123";

        public static final String ADMIN = "admin";
        public static final String ADMIN_PASSWORD = "admin123";

        public static final String MANAGER = "manager";
        public static final String MANAGER_PASSWORD = "manager123";

        public static final String EMPLOYEE = "employee";
        public static final String EMPLOYEE_PASSWORD = "employee123";

        public static final String INVALID_USER = "nonexistent";
        public static final String INVALID_PASSWORD = "wrongpassword";
    }

    // ==================== PRODUCTS ====================

    public static class Products {
        public static String uniqueName() {
            String name = "Test Product " + UUID.randomUUID().toString().substring(0, 8);
            Allure.parameter("productName", name);
            return name;
        }

        public static String uniqueName(String prefix) {
            String name = prefix + " " + UUID.randomUUID().toString().substring(0, 8);
            Allure.parameter("productName", name);
            return name;
        }

        public static final int DEFAULT_QUANTITY = 100;
        public static final double DEFAULT_PRICE = 49.99;

        public static final int ZERO_QUANTITY = 0;
        public static final double ZERO_PRICE = 0.0;

        public static final String EMPTY_NAME = "";
        public static final String VERY_LONG_NAME = "A".repeat(300);
    }

    // ==================== MESSAGES ====================

    public static class Messages {
        public static final String INVALID_CREDENTIALS = "Invalid username or password";
        public static final String UNAUTHORIZED = "Unauthorized";
        public static final String ACCESS_DENIED = "Access Denied";
    }
}