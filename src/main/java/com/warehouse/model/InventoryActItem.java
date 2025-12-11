package com.warehouse.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Позиция акта инвентаризации
 * WH-275: Inventory Acts
 */
@Entity
@Table(name = "inventory_act_items")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class InventoryActItem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Акт инвентаризации
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "inventory_act_id", nullable = false)
    private InventoryAct inventoryAct;

    /**
     * Товар
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id", nullable = false)
    private Product product;

    /**
     * Ожидаемое количество (из системы)
     */
    @Column(name = "expected_quantity", nullable = false)
    private Integer expectedQuantity;

    /**
     * Фактическое количество (посчитанное)
     */
    @Column(name = "actual_quantity", nullable = false)
    private Integer actualQuantity;

    /**
     * Разница (calculated: actual - expected)
     * NOTE: В базе это GENERATED column, здесь для удобства работы с entity
     */
    @Transient
    public Integer getDifference() {
        return actualQuantity - expectedQuantity;
    }
}
