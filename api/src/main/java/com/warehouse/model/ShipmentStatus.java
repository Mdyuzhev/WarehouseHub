package com.warehouse.model;

/**
 * Статусы расходной накладной
 * WH-273: Shipment Documents
 */
public enum ShipmentStatus {
    /** Черновик - создан, но не утверждён */
    DRAFT("Черновик"),

    /** Утверждён - проверен, stock зарезервирован */
    APPROVED("Утверждён"),

    /** Отгружен - товар списан со stock */
    SHIPPED("Отгружен"),

    /** Доставлен - финальный статус */
    DELIVERED("Доставлен");

    private final String displayName;

    ShipmentStatus(String displayName) {
        this.displayName = displayName;
    }

    public String getDisplayName() {
        return displayName;
    }
}
