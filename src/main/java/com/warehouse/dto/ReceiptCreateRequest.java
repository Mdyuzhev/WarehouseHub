package com.warehouse.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Request DTO для создания приходной накладной
 * WH-272: Receipt Documents
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReceiptCreateRequest {

    @NotNull(message = "Facility ID is required")
    private Long facilityId;

    private String supplierName;

    private String notes;

    @NotNull(message = "Items are required")
    @Size(min = 1, message = "At least one item is required")
    private List<ReceiptItemRequest> items;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ReceiptItemRequest {
        @NotNull(message = "Product ID is required")
        private Long productId;

        @NotNull(message = "Expected quantity is required")
        private Integer expectedQuantity;
    }
}
