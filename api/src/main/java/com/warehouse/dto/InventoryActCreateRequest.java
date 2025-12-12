package com.warehouse.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Request DTO для создания акта инвентаризации
 * WH-275: Inventory Acts
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class InventoryActCreateRequest {

    @NotNull(message = "Facility ID is required")
    private Long facilityId;

    private String notes;

    @NotNull(message = "Items are required")
    @Size(min = 1, message = "At least one item is required")
    private List<InventoryActItemRequest> items;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class InventoryActItemRequest {
        @NotNull(message = "Product ID is required")
        private Long productId;

        @NotNull(message = "Expected quantity is required")
        private Integer expectedQuantity;

        @NotNull(message = "Actual quantity is required")
        private Integer actualQuantity;
    }
}
