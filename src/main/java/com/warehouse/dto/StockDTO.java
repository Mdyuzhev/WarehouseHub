package com.warehouse.dto;

import lombok.*;

/**
 * DTO для остатков товаров
 * WH-270: Product/Stock Separation
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class StockDTO {
    private Long id;
    private Long productId;
    private String productName;
    private Long facilityId;
    private String facilityCode;
    private String facilityName;
    private Integer quantity;
    private Integer reserved;
    private Integer available;
}
