package com.warehouse.model;

/**
 * Статусы приходной накладной
 * WH-272: Receipt Documents
 */
public enum ReceiptStatus {
    /** Черновик - создан, но не подтвержден */
    DRAFT("Черновик"),

    /** Утвержден - проверен менеджером */
    APPROVED("Утвержден"),

    /** Подтвержден - товар принят, stock обновлен */
    CONFIRMED("Подтвержден"),

    /** Завершен - финальный статус */
    COMPLETED("Завершен");

    private final String displayName;

    ReceiptStatus(String displayName) {
        this.displayName = displayName;
    }

    public String getDisplayName() {
        return displayName;
    }
}
