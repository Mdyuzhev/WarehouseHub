package com.warehouse.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/**
 * Stock notification for Kafka warehouse.notifications topic.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StockNotification {
    private String notificationId;
    private String notificationType; // LOW_STOCK, OUT_OF_STOCK
    private Long productId;
    private String productName;
    private String category;
    private Integer currentQuantity;
    private Integer threshold;
    private String message;
    private Instant timestamp;
}
