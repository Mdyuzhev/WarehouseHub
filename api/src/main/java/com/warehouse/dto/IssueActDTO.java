package com.warehouse.dto;

import com.warehouse.model.IssueStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * DTO для акта выдачи
 * WH-275: Issue Acts
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class IssueActDTO {
    private Long id;
    private String documentNumber;

    // Facility info
    private Long facilityId;
    private String facilityCode;
    private String facilityName;

    // Customer
    private String customerName;
    private String customerPhone;

    // Status
    private IssueStatus status;
    private String notes;

    // Created
    private LocalDateTime createdAt;
    private String createdByUsername;

    // Completed
    private LocalDateTime completedAt;

    // Items
    @Builder.Default
    private List<IssueActItemDTO> items = new ArrayList<>();

    // Computed fields
    private Integer totalQuantity;
}
