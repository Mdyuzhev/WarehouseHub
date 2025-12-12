package com.warehouse.model;

/**
 * Типы объектов логистической сети
 *
 * DC - Distribution Center (Распределительный центр)
 * WH - Warehouse (Склад)
 * PP - Pickup Point (Пункт выдачи)
 */
public enum FacilityType {
    DC("Распределительный центр"),
    WH("Склад"),
    PP("Пункт выдачи");

    private final String displayName;

    FacilityType(String displayName) {
        this.displayName = displayName;
    }

    public String getDisplayName() {
        return displayName;
    }
}
