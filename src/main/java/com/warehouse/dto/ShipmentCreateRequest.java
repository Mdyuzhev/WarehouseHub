package com.warehouse.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Request DTO для создания расходной накладной
 * WH-273: Shipment Documents
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ShipmentCreateRequest {

    @NotNull(message = "Source Facility ID is required")
    private Long sourceFacilityId;

    private Long destinationFacilityId;

    private String destinationAddress;

    private String notes;

    @NotNull(message = "Items are required")
    @Size(min = 1, message = "At least one item is required")
    private List<ShipmentItemRequest> items;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ShipmentItemRequest {
        @NotNull(message = "Product ID is required")
        private Long productId;

        @NotNull(message = "Quantity is required")
        private Integer quantity;
    }
}
