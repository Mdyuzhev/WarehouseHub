package com.warehouse.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO для позиции приходной накладной
 * WH-272: Receipt Documents
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReceiptItemDTO {
    private Long id;
    private Long productId;
    private String productName;
    private Integer expectedQuantity;
    private Integer actualQuantity;
}
