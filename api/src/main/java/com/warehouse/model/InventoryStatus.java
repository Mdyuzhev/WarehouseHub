package com.warehouse.model;

/**
 * Статус акта инвентаризации
 * WH-275: Inventory Acts
 *
 * Простой flow: DRAFT → COMPLETED
 */
public enum InventoryStatus {
    /**
     * Черновик (данные вносятся)
     */
    DRAFT,

    /**
     * Завершена (корректировка остатков применена)
     */
    COMPLETED
}
