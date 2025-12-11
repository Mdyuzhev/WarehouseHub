package com.warehouse.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO для позиции расходной накладной
 * WH-273: Shipment Documents
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ShipmentItemDTO {
    private Long id;
    private Long productId;
    private String productName;
    private Integer quantity;
}
