package com.warehouse.dto;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Request DTO для подтверждения приходной накладной
 * WH-272: Receipt Documents
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReceiptConfirmRequest {

    @NotNull(message = "Items with actual quantities are required")
    private List<ItemActualQuantity> items;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ItemActualQuantity {
        @NotNull(message = "Item ID is required")
        private Long itemId;

        @NotNull(message = "Actual quantity is required")
        private Integer actualQuantity;
    }
}
