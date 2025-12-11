package com.warehouse.dto;

import com.warehouse.model.InventoryStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * DTO для акта инвентаризации
 * WH-275: Inventory Acts
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class InventoryActDTO {
    private Long id;
    private String documentNumber;

    // Facility info
    private Long facilityId;
    private String facilityCode;
    private String facilityName;

    // Status
    private InventoryStatus status;
    private String notes;

    // Created
    private LocalDateTime createdAt;
    private String createdByUsername;

    // Completed
    private LocalDateTime completedAt;
    private String completedByUsername;

    // Items
    @Builder.Default
    private List<InventoryActItemDTO> items = new ArrayList<>();

    // Computed fields
    private Integer totalExpected;
    private Integer totalActual;
    private Integer totalDifference;
}
