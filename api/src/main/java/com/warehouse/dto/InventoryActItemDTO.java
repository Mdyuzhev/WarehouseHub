package com.warehouse.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO для позиции акта инвентаризации
 * WH-275: Inventory Acts
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class InventoryActItemDTO {
    private Long id;
    private Long productId;
    private String productName;
    private Integer expectedQuantity;
    private Integer actualQuantity;
    private Integer difference; // actual - expected
}
