package com.warehouse.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO для позиции акта выдачи
 * WH-275: Issue Acts
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class IssueActItemDTO {
    private Long id;
    private Long productId;
    private String productName;
    private Integer quantity;
}
