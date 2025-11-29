package com.warehouse.service;

import com.warehouse.config.KafkaConfig;
import com.warehouse.dto.StockNotification;
import com.warehouse.model.Product;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.UUID;

/**
 * Stock Notification Service - sends low stock alerts to Kafka.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class StockNotificationService {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    @Value("${stock.low-threshold:10}")
    private int lowStockThreshold;

    @Value("${stock.out-threshold:0}")
    private int outOfStockThreshold;

    /**
     * Check product stock level and send notification if needed.
     */
    @Async
    public void checkAndNotify(Product product) {
        if (product.getQuantity() <= outOfStockThreshold) {
            sendNotification(buildNotification(product, "OUT_OF_STOCK",
                    "Product is out of stock!"));
        } else if (product.getQuantity() <= lowStockThreshold) {
            sendNotification(buildNotification(product, "LOW_STOCK",
                    String.format("Low stock alert! Only %d items remaining.", product.getQuantity())));
        }
    }

    private StockNotification buildNotification(Product product, String type, String message) {
        return StockNotification.builder()
                .notificationId(UUID.randomUUID().toString())
                .notificationType(type)
                .productId(product.getId())
                .productName(product.getName())
                .category(product.getCategory())
                .currentQuantity(product.getQuantity())
                .threshold(type.equals("OUT_OF_STOCK") ? outOfStockThreshold : lowStockThreshold)
                .message(message)
                .timestamp(Instant.now())
                .build();
    }

    private void sendNotification(StockNotification notification) {
        try {
            kafkaTemplate.send(KafkaConfig.NOTIFICATIONS_TOPIC,
                    notification.getProductId().toString(), notification)
                    .whenComplete((result, ex) -> {
                        if (ex != null) {
                            log.error("Failed to send stock notification: {}", ex.getMessage());
                        } else {
                            log.info("Stock notification sent: {} - {} (qty: {})",
                                    notification.getNotificationType(),
                                    notification.getProductName(),
                                    notification.getCurrentQuantity());
                        }
                    });
        } catch (Exception e) {
            log.error("Error sending stock notification: {}", e.getMessage());
        }
    }
}
