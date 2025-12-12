package com.warehouse.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Request DTO для создания акта выдачи
 * WH-275: Issue Acts
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class IssueActCreateRequest {

    @NotNull(message = "Facility ID is required")
    private Long facilityId;

    @NotBlank(message = "Customer name is required")
    private String customerName;

    private String customerPhone;

    private String notes;

    @NotNull(message = "Items are required")
    @Size(min = 1, message = "At least one item is required")
    private List<IssueActItemRequest> items;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class IssueActItemRequest {
        @NotNull(message = "Product ID is required")
        private Long productId;

        @NotNull(message = "Quantity is required")
        private Integer quantity;
    }
}
