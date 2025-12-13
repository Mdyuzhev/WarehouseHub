package com.warehouse.service;

import com.warehouse.config.KafkaConfig;
import com.warehouse.dto.ShipmentEvent;
import com.warehouse.dto.ShipmentItemDTO;
import com.warehouse.model.*;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.ProductRepository;
import com.warehouse.repository.ReceiptDocumentRepository;
import com.warehouse.repository.ShipmentDocumentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Consumer для логистических событий
 * WH-274: Kafka Auto-Documents - Блок 3
 *
 * Логика:
 * - При SHIPMENT_DISPATCHED → автоматически создаёт Receipt на destination facility
 * - При SHIPMENT_DELIVERED → обновляет статус shipment
 */
@Service
@ConditionalOnBean(KafkaTemplate.class)
@RequiredArgsConstructor
@Slf4j
public class LogisticsEventConsumer {

    private final ShipmentDocumentRepository shipmentRepository;
    private final ReceiptDocumentRepository receiptRepository;
    private final FacilityRepository facilityRepository;
    private final ProductRepository productRepository;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");

    /**
     * Consumer для shipment events
     * При DISPATCHED → создаёт Receipt на destination facility
     */
    @KafkaListener(
            topics = KafkaConfig.SHIPMENTS_TOPIC,
            groupId = "warehouse-logistics-group",
            containerFactory = "kafkaListenerContainerFactory"
    )
    @Transactional
    public void handleShipmentEvent(ShipmentEvent event) {
        log.info("Received shipment event: {} for shipment {}", event.getEventType(), event.getShipmentId());

        if ("DISPATCHED".equals(event.getEventType())) {
            handleShipmentDispatched(event);
        } else if ("DELIVERED".equals(event.getEventType())) {
            handleShipmentDelivered(event);
        }
    }

    /**
     * Обработка DISPATCHED события
     * Создаёт Receipt на destination facility
     */
    @SuppressWarnings("null")
    private void handleShipmentDispatched(ShipmentEvent event) {
        try {
            // Find destination facility
            Long destFacilityId = java.util.Objects.requireNonNull(event.getDestinationFacilityId());
            Facility destinationFacility = facilityRepository.findById(destFacilityId)
                    .orElseThrow(() -> new IllegalArgumentException(
                            "Destination facility not found: " + event.getDestinationFacilityId()));

            // Find shipment
            Long shipmentId = java.util.Objects.requireNonNull(event.getShipmentId());
            ShipmentDocument shipment = shipmentRepository.findById(shipmentId)
                    .orElseThrow(() -> new IllegalArgumentException(
                            "Shipment not found: " + event.getShipmentId()));

            // Generate document number for receipt
            String receiptNumber = generateReceiptNumber(destinationFacility);

            // Create receipt document
            ReceiptDocument receipt = ReceiptDocument.builder()
                    .documentNumber(receiptNumber)
                    .facility(destinationFacility)
                    .sourceShipment(shipment)
                    .supplierName("Transfer from " + shipment.getSourceFacility().getName() + " (" + event.getDocumentNumber() + ")")
                    .status(ReceiptStatus.APPROVED) // Auto-approve for internal transfers
                    .notes("Auto-created from shipment " + event.getDocumentNumber())
                    .build();

            // Add items from shipment
            for (ShipmentItemDTO shipmentItem : event.getItems()) {
                Long productId = java.util.Objects.requireNonNull(shipmentItem.getProductId());
                Product product = productRepository.findById(productId)
                        .orElseThrow(() -> new IllegalArgumentException(
                                "Product not found: " + shipmentItem.getProductId()));

                ReceiptItem receiptItem = ReceiptItem.builder()
                        .product(product)
                        .expectedQuantity(shipmentItem.getQuantity())
                        .actualQuantity(0) // Will be set during confirmation
                        .build();

                receipt.addItem(receiptItem);
            }

            ReceiptDocument savedReceipt = java.util.Objects.requireNonNull(receiptRepository.save(receipt));
            log.info("Auto-created receipt {} for shipment {} at facility {}",
                    savedReceipt.getDocumentNumber(), event.getDocumentNumber(), destinationFacility.getCode());

        } catch (Exception e) {
            log.error("Failed to auto-create receipt for shipment {}: {}",
                    event.getShipmentId(), e.getMessage(), e);
        }
    }

    /**
     * Обработка DELIVERED события
     * Обновляет статус shipment на DELIVERED
     */
    private void handleShipmentDelivered(ShipmentEvent event) {
        try {
            Long shipmentId = java.util.Objects.requireNonNull(event.getShipmentId());
            ShipmentDocument shipment = shipmentRepository.findById(shipmentId)
                    .orElseThrow(() -> new IllegalArgumentException(
                            "Shipment not found: " + event.getShipmentId()));

            if (shipment.getStatus() == ShipmentStatus.SHIPPED) {
                shipment.setStatus(ShipmentStatus.DELIVERED);
                shipment.setDeliveredAt(LocalDateTime.now());
                shipmentRepository.save(shipment);

                log.info("Shipment {} marked as DELIVERED", event.getDocumentNumber());
            }
        } catch (Exception e) {
            log.error("Failed to update shipment {} to DELIVERED: {}",
                    event.getShipmentId(), e.getMessage(), e);
        }
    }

    /**
     * Генерация номера receipt документа
     * Формат: RCP-{facilityCode}-{YYYYMMDD}-{seq}
     */
    private String generateReceiptNumber(Facility facility) {
        LocalDate today = LocalDate.now();
        LocalDateTime startOfDay = today.atStartOfDay();
        LocalDateTime endOfDay = today.plusDays(1).atStartOfDay();

        Long count = receiptRepository.countByFacilityAndDate(
                facility.getId(),
                startOfDay,
                endOfDay
        );

        int sequence = count.intValue() + 1;
        String dateStr = DATE_FORMATTER.format(today);

        return String.format("RCP-%s-%s-%03d", facility.getCode(), dateStr, sequence);
    }
}
