package com.warehouse.dto;

import com.warehouse.model.ShipmentStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * DTO для расходной накладной
 * WH-273: Shipment Documents
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ShipmentDocumentDTO {
    private Long id;
    private String documentNumber;

    // Source facility
    private Long sourceFacilityId;
    private String sourceFacilityCode;
    private String sourceFacilityName;

    // Destination facility (optional, может быть внешний адрес)
    private Long destinationFacilityId;
    private String destinationFacilityCode;
    private String destinationFacilityName;
    private String destinationAddress;

    // Status
    private ShipmentStatus status;
    private String notes;

    // Created
    private LocalDateTime createdAt;
    private String createdByUsername;

    // Approved
    private LocalDateTime approvedAt;
    private String approvedByUsername;

    // Shipped
    private LocalDateTime shippedAt;
    private String shippedByUsername;

    // Delivered
    private LocalDateTime deliveredAt;

    // Items
    @Builder.Default
    private List<ShipmentItemDTO> items = new ArrayList<>();

    // Computed fields
    private Integer totalQuantity;
}
