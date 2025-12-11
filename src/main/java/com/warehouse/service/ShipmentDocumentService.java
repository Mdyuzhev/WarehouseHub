package com.warehouse.service;

import com.warehouse.dto.ShipmentCreateRequest;
import com.warehouse.dto.ShipmentDocumentDTO;
import com.warehouse.dto.ShipmentItemDTO;
import com.warehouse.model.*;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.ProductRepository;
import com.warehouse.repository.ShipmentDocumentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Сервис для работы с расходными накладными
 * WH-273: Shipment Documents
 *
 * State Machine: DRAFT → APPROVED → SHIPPED → DELIVERED
 * - APPROVED: reserve stock (stock.reserved += quantity)
 * - SHIPPED: deduct stock (stock.quantity -= quantity, stock.reserved -= quantity)
 * - CANCEL: release reservation
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ShipmentDocumentService {

    private final ShipmentDocumentRepository shipmentRepository;
    private final FacilityRepository facilityRepository;
    private final ProductRepository productRepository;
    private final StockService stockService;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");

    /**
     * Создать расходную накладную (DRAFT)
     */
    @Transactional
    public ShipmentDocumentDTO create(ShipmentCreateRequest request, User currentUser) {
        log.info("Creating shipment document from facility {}", request.getSourceFacilityId());

        // Validate source facility
        Facility sourceFacility = facilityRepository.findById(request.getSourceFacilityId())
                .orElseThrow(() -> new IllegalArgumentException("Source facility not found: " + request.getSourceFacilityId()));

        // Validate destination (either facility or address)
        Facility destinationFacility = null;
        if (request.getDestinationFacilityId() != null) {
            destinationFacility = facilityRepository.findById(request.getDestinationFacilityId())
                    .orElseThrow(() -> new IllegalArgumentException("Destination facility not found: " + request.getDestinationFacilityId()));
        } else if (request.getDestinationAddress() == null || request.getDestinationAddress().isBlank()) {
            throw new IllegalArgumentException("Either destination facility or address must be provided");
        }

        // Validate items
        if (request.getItems() == null || request.getItems().isEmpty()) {
            throw new IllegalArgumentException("Shipment must have at least one item");
        }

        // Generate document number
        String documentNumber = generateDocumentNumber(sourceFacility);

        // Create document
        ShipmentDocument shipment = ShipmentDocument.builder()
                .documentNumber(documentNumber)
                .sourceFacility(sourceFacility)
                .destinationFacility(destinationFacility)
                .destinationAddress(request.getDestinationAddress())
                .notes(request.getNotes())
                .status(ShipmentStatus.DRAFT)
                .createdBy(currentUser)
                .build();

        // Add items
        for (ShipmentCreateRequest.ShipmentItemRequest itemRequest : request.getItems()) {
            Product product = productRepository.findById(itemRequest.getProductId())
                    .orElseThrow(() -> new IllegalArgumentException("Product not found: " + itemRequest.getProductId()));

            ShipmentItem item = ShipmentItem.builder()
                    .product(product)
                    .quantity(itemRequest.getQuantity())
                    .build();

            shipment.addItem(item);
        }

        shipment = shipmentRepository.save(shipment);
        log.info("Shipment document created: {}", documentNumber);

        return toDTO(shipment);
    }

    /**
     * Получить документ по ID
     */
    @Transactional(readOnly = true)
    public ShipmentDocumentDTO getById(Long id) {
        ShipmentDocument shipment = shipmentRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Shipment not found: " + id));
        return toDTO(shipment);
    }

    /**
     * Получить все документы по объекту-источнику
     */
    @Transactional(readOnly = true)
    public List<ShipmentDocumentDTO> getBySourceFacility(Long facilityId) {
        List<ShipmentDocument> shipments = shipmentRepository.findBySourceFacilityId(facilityId);
        return shipments.stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    /**
     * Утвердить документ: DRAFT → APPROVED
     * Резервирует stock
     */
    @Transactional
    public ShipmentDocumentDTO approve(Long id, User currentUser) {
        log.info("Approving shipment document {}", id);

        ShipmentDocument shipment = shipmentRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Shipment not found: " + id));

        // Validate state
        if (shipment.getStatus() != ShipmentStatus.DRAFT) {
            throw new IllegalStateException("Only DRAFT shipments can be approved. Current status: " + shipment.getStatus());
        }

        // Validate items
        if (shipment.getItems().isEmpty()) {
            throw new IllegalStateException("Cannot approve shipment without items");
        }

        // Reserve stock for each item
        for (ShipmentItem item : shipment.getItems()) {
            try {
                stockService.reserve(
                        item.getProduct().getId(),
                        shipment.getSourceFacility().getId(),
                        item.getQuantity()
                );
                log.info("Reserved {} units of product {} at facility {}",
                        item.getQuantity(),
                        item.getProduct().getId(),
                        shipment.getSourceFacility().getCode());
            } catch (Exception e) {
                log.error("Failed to reserve stock for item {}: {}", item.getId(), e.getMessage());
                throw new RuntimeException("Failed to reserve stock: " + e.getMessage(), e);
            }
        }

        // Update status
        shipment.setStatus(ShipmentStatus.APPROVED);
        shipment.setApprovedBy(currentUser);
        shipment.setApprovedAt(LocalDateTime.now());

        shipment = shipmentRepository.save(shipment);
        log.info("Shipment {} approved by user {}, stock reserved", shipment.getDocumentNumber(), currentUser.getUsername());

        return toDTO(shipment);
    }

    /**
     * Отгрузить документ: APPROVED → SHIPPED
     * Списывает stock (quantity и reserved)
     */
    @Transactional
    public ShipmentDocumentDTO ship(Long id, User currentUser) {
        log.info("Shipping shipment document {}", id);

        ShipmentDocument shipment = shipmentRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Shipment not found: " + id));

        // Validate state
        if (shipment.getStatus() != ShipmentStatus.APPROVED) {
            throw new IllegalStateException("Only APPROVED shipments can be shipped. Current status: " + shipment.getStatus());
        }

        // Ship items (deduct from stock)
        for (ShipmentItem item : shipment.getItems()) {
            try {
                // Release reservation and deduct stock
                stockService.releaseReservation(
                        item.getProduct().getId(),
                        shipment.getSourceFacility().getId(),
                        item.getQuantity(),
                        true // shipped = true (deduct stock)
                );
                log.info("Shipped {} units of product {} from facility {}",
                        item.getQuantity(),
                        item.getProduct().getId(),
                        shipment.getSourceFacility().getCode());
            } catch (Exception e) {
                log.error("Failed to ship item {}: {}", item.getId(), e.getMessage());
                throw new RuntimeException("Failed to ship stock: " + e.getMessage(), e);
            }
        }

        // Update status
        shipment.setStatus(ShipmentStatus.SHIPPED);
        shipment.setShippedBy(currentUser);
        shipment.setShippedAt(LocalDateTime.now());

        shipment = shipmentRepository.save(shipment);
        log.info("Shipment {} shipped by user {}, stock deducted", shipment.getDocumentNumber(), currentUser.getUsername());

        return toDTO(shipment);
    }

    /**
     * Доставить документ: SHIPPED → DELIVERED
     */
    @Transactional
    public ShipmentDocumentDTO deliver(Long id) {
        log.info("Delivering shipment document {}", id);

        ShipmentDocument shipment = shipmentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Shipment not found: " + id));

        // Validate state
        if (shipment.getStatus() != ShipmentStatus.SHIPPED) {
            throw new IllegalStateException("Only SHIPPED shipments can be delivered. Current status: " + shipment.getStatus());
        }

        // Update status
        shipment.setStatus(ShipmentStatus.DELIVERED);
        shipment.setDeliveredAt(LocalDateTime.now());
        shipment = shipmentRepository.save(shipment);

        log.info("Shipment {} delivered", shipment.getDocumentNumber());

        return toDTO(shipment);
    }

    /**
     * Отменить документ
     * Снимает резервирование stock если был APPROVED
     */
    @Transactional
    public void cancel(Long id) {
        log.info("Cancelling shipment document {}", id);

        ShipmentDocument shipment = shipmentRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Shipment not found: " + id));

        // Can only cancel DRAFT or APPROVED
        if (shipment.getStatus() != ShipmentStatus.DRAFT && shipment.getStatus() != ShipmentStatus.APPROVED) {
            throw new IllegalStateException("Only DRAFT or APPROVED shipments can be cancelled. Current status: " + shipment.getStatus());
        }

        // Release reservations if APPROVED
        if (shipment.getStatus() == ShipmentStatus.APPROVED) {
            for (ShipmentItem item : shipment.getItems()) {
                try {
                    stockService.releaseReservation(
                            item.getProduct().getId(),
                            shipment.getSourceFacility().getId(),
                            item.getQuantity(),
                            false // not shipped
                    );
                    log.info("Released reservation for {} units of product {} at facility {}",
                            item.getQuantity(),
                            item.getProduct().getId(),
                            shipment.getSourceFacility().getCode());
                } catch (Exception e) {
                    log.error("Failed to release reservation for item {}: {}", item.getId(), e.getMessage());
                    throw new RuntimeException("Failed to release reservation: " + e.getMessage(), e);
                }
            }
        }

        shipmentRepository.delete(shipment);
        log.info("Shipment {} cancelled", shipment.getDocumentNumber());
    }

    /**
     * Генерация номера документа
     * Формат: SHP-{sourceFacilityCode}-{YYYYMMDD}-{seq}
     * Пример: SHP-WH-C-001-20251211-001
     */
    private String generateDocumentNumber(Facility facility) {
        LocalDate today = LocalDate.now();
        LocalDateTime startOfDay = today.atStartOfDay();
        LocalDateTime endOfDay = today.plusDays(1).atStartOfDay();

        Long count = shipmentRepository.countByFacilityAndDate(
                facility.getId(),
                startOfDay,
                endOfDay
        );

        int sequence = count.intValue() + 1;
        String dateStr = DATE_FORMATTER.format(today);

        return String.format("SHP-%s-%s-%03d", facility.getCode(), dateStr, sequence);
    }

    /**
     * Преобразовать Entity в DTO
     */
    private ShipmentDocumentDTO toDTO(ShipmentDocument shipment) {
        List<ShipmentItemDTO> itemDTOs = shipment.getItems().stream()
                .map(item -> ShipmentItemDTO.builder()
                        .id(item.getId())
                        .productId(item.getProduct().getId())
                        .productName(item.getProduct().getName())
                        .quantity(item.getQuantity())
                        .build())
                .collect(Collectors.toList());

        Integer totalQuantity = shipment.getItems().stream()
                .mapToInt(ShipmentItem::getQuantity)
                .sum();

        return ShipmentDocumentDTO.builder()
                .id(shipment.getId())
                .documentNumber(shipment.getDocumentNumber())
                .sourceFacilityId(shipment.getSourceFacility().getId())
                .sourceFacilityCode(shipment.getSourceFacility().getCode())
                .sourceFacilityName(shipment.getSourceFacility().getName())
                .destinationFacilityId(shipment.getDestinationFacility() != null ? shipment.getDestinationFacility().getId() : null)
                .destinationFacilityCode(shipment.getDestinationFacility() != null ? shipment.getDestinationFacility().getCode() : null)
                .destinationFacilityName(shipment.getDestinationFacility() != null ? shipment.getDestinationFacility().getName() : null)
                .destinationAddress(shipment.getDestinationAddress())
                .status(shipment.getStatus())
                .notes(shipment.getNotes())
                .createdAt(shipment.getCreatedAt())
                .createdByUsername(shipment.getCreatedBy() != null ? shipment.getCreatedBy().getUsername() : null)
                .approvedAt(shipment.getApprovedAt())
                .approvedByUsername(shipment.getApprovedBy() != null ? shipment.getApprovedBy().getUsername() : null)
                .shippedAt(shipment.getShippedAt())
                .shippedByUsername(shipment.getShippedBy() != null ? shipment.getShippedBy().getUsername() : null)
                .deliveredAt(shipment.getDeliveredAt())
                .items(itemDTOs)
                .totalQuantity(totalQuantity)
                .build();
    }
}
