package com.warehouse.dto;

import com.warehouse.model.ReceiptStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * DTO для приходной накладной
 * WH-272: Receipt Documents
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReceiptDocumentDTO {
    private Long id;
    private String documentNumber;

    // Facility info
    private Long facilityId;
    private String facilityCode;
    private String facilityName;

    // Supplier
    private String supplierName;

    // Status
    private ReceiptStatus status;
    private String notes;

    // Created
    private LocalDateTime createdAt;
    private String createdByUsername;

    // Approved
    private LocalDateTime approvedAt;
    private String approvedByUsername;

    // Confirmed
    private LocalDateTime confirmedAt;
    private String confirmedByUsername;

    // Items
    @Builder.Default
    private List<ReceiptItemDTO> items = new ArrayList<>();

    // Computed fields
    private Integer totalExpected;
    private Integer totalActual;
}
