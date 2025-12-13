package com.warehouse.service;

import com.warehouse.config.KafkaConfig;
import com.warehouse.dto.ShipmentEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

/**
 * Producer для логистических событий
 * WH-274: Kafka Auto-Documents - Блок 2
 */
@Service
@ConditionalOnBean(KafkaTemplate.class)
@Slf4j
public class LogisticsEventProducer {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    @Autowired
    public LogisticsEventProducer(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
        log.info("LogisticsEventProducer initialized with Kafka");
    }

    /**
     * Отправить событие "Shipment dispatched" (SHIPPED)
     * Триггерит авто-создание Receipt на destination facility
     */
    @Async
    @SuppressWarnings("null")
    public void sendShipmentDispatched(ShipmentEvent event) {
        try {
            String key = java.util.Objects.requireNonNull(event.getShipmentId()).toString();
            kafkaTemplate.send(KafkaConfig.SHIPMENTS_TOPIC, key, event)
            .whenComplete((result, ex) -> {
                if (ex != null) {
                    log.error("Failed to send shipment dispatched event for shipment {}: {}",
                            event.getShipmentId(), ex.getMessage());
                } else {
                    log.info("Shipment dispatched event sent: {} ({})",
                            event.getDocumentNumber(), event.getShipmentId());
                }
            });
        } catch (Exception e) {
            log.error("Error sending shipment dispatched event: {}", e.getMessage());
        }
    }

    /**
     * Отправить событие "Shipment delivered" (Receipt confirmed)
     */
    @Async
    @SuppressWarnings("null")
    public void sendShipmentDelivered(Long shipmentId, String documentNumber) {
        try {
            ShipmentEvent event = ShipmentEvent.builder()
                    .eventType("DELIVERED")
                    .shipmentId(shipmentId)
                    .documentNumber(documentNumber)
                    .build();

            String key = java.util.Objects.requireNonNull(shipmentId).toString();
            kafkaTemplate.send(KafkaConfig.SHIPMENTS_TOPIC, key, event)
            .whenComplete((result, ex) -> {
                if (ex != null) {
                    log.error("Failed to send shipment delivered event for shipment {}: {}",
                            shipmentId, ex.getMessage());
                } else {
                    log.info("Shipment delivered event sent: {} ({})", documentNumber, shipmentId);
                }
            });
        } catch (Exception e) {
            log.error("Error sending shipment delivered event: {}", e.getMessage());
        }
    }
}
