package com.warehouse.service;

import com.warehouse.dto.*;
import com.warehouse.model.*;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.ProductRepository;
import com.warehouse.repository.ReceiptDocumentRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Сервис для работы с приходными накладными
 * WH-272: Receipt Documents
 *
 * State Machine: DRAFT → APPROVED → CONFIRMED → COMPLETED
 */
@Service
@Slf4j
public class ReceiptDocumentService {

    private final ReceiptDocumentRepository receiptRepository;
    private final FacilityRepository facilityRepository;
    private final ProductRepository productRepository;
    private final StockService stockService;
    private final LogisticsEventProducer logisticsEventProducer;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");

    @Autowired
    public ReceiptDocumentService(ReceiptDocumentRepository receiptRepository,
                                  FacilityRepository facilityRepository,
                                  ProductRepository productRepository,
                                  StockService stockService,
                                  @Autowired(required = false) LogisticsEventProducer logisticsEventProducer) {
        this.receiptRepository = receiptRepository;
        this.facilityRepository = facilityRepository;
        this.productRepository = productRepository;
        this.stockService = stockService;
        this.logisticsEventProducer = logisticsEventProducer;
    }

    /**
     * Создать приходную накладную (DRAFT)
     */
    @Transactional
    public ReceiptDocumentDTO create(ReceiptCreateRequest request, User currentUser) {
        log.info("Creating receipt document for facility {}", request.getFacilityId());

        // Validate facility
        Facility facility = facilityRepository.findById(request.getFacilityId())
                .orElseThrow(() -> new IllegalArgumentException("Facility not found: " + request.getFacilityId()));

        // Validate items
        if (request.getItems() == null || request.getItems().isEmpty()) {
            throw new IllegalArgumentException("Receipt must have at least one item");
        }

        // Generate document number
        String documentNumber = generateDocumentNumber(facility);

        // Create document
        ReceiptDocument receipt = ReceiptDocument.builder()
                .documentNumber(documentNumber)
                .facility(facility)
                .supplierName(request.getSupplierName())
                .notes(request.getNotes())
                .status(ReceiptStatus.DRAFT)
                .createdBy(currentUser)
                .build();

        // Add items
        for (ReceiptCreateRequest.ReceiptItemRequest itemRequest : request.getItems()) {
            Product product = productRepository.findById(itemRequest.getProductId())
                    .orElseThrow(() -> new IllegalArgumentException("Product not found: " + itemRequest.getProductId()));

            ReceiptItem item = ReceiptItem.builder()
                    .product(product)
                    .expectedQuantity(itemRequest.getExpectedQuantity())
                    .actualQuantity(0)
                    .build();

            receipt.addItem(item);
        }

        receipt = receiptRepository.save(receipt);
        log.info("Receipt document created: {}", documentNumber);

        return toDTO(receipt);
    }

    /**
     * Получить документ по ID
     */
    @Transactional(readOnly = true)
    public ReceiptDocumentDTO getById(Long id) {
        ReceiptDocument receipt = receiptRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Receipt not found: " + id));
        return toDTO(receipt);
    }

    /**
     * Получить все документы по объекту
     */
    @Transactional(readOnly = true)
    public List<ReceiptDocumentDTO> getByFacility(Long facilityId) {
        List<ReceiptDocument> receipts = receiptRepository.findByFacilityId(facilityId);
        return receipts.stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    /**
     * Утвердить документ: DRAFT → APPROVED
     */
    @Transactional
    public ReceiptDocumentDTO approve(Long id, User currentUser) {
        log.info("Approving receipt document {}", id);

        ReceiptDocument receipt = receiptRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Receipt not found: " + id));

        // Validate state
        if (receipt.getStatus() != ReceiptStatus.DRAFT) {
            throw new IllegalStateException("Only DRAFT receipts can be approved. Current status: " + receipt.getStatus());
        }

        // Validate items
        if (receipt.getItems().isEmpty()) {
            throw new IllegalStateException("Cannot approve receipt without items");
        }

        // Update status
        receipt.setStatus(ReceiptStatus.APPROVED);
        receipt.setApprovedBy(currentUser);
        receipt.setApprovedAt(LocalDateTime.now());

        receipt = receiptRepository.save(receipt);
        log.info("Receipt {} approved by user {}", receipt.getDocumentNumber(), currentUser.getUsername());

        return toDTO(receipt);
    }

    /**
     * Подтвердить документ: APPROVED → CONFIRMED
     * Обновляет stock на основе actualQuantity
     */
    @Transactional
    public ReceiptDocumentDTO confirm(Long id, ReceiptConfirmRequest request, User currentUser) {
        log.info("Confirming receipt document {}", id);

        ReceiptDocument receipt = receiptRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Receipt not found: " + id));

        // Validate state
        if (receipt.getStatus() != ReceiptStatus.APPROVED) {
            throw new IllegalStateException("Only APPROVED receipts can be confirmed. Current status: " + receipt.getStatus());
        }

        // Update actual quantities
        for (ReceiptConfirmRequest.ItemActualQuantity actualQty : request.getItems()) {
            ReceiptItem item = receipt.getItems().stream()
                    .filter(i -> i.getId().equals(actualQty.getItemId()))
                    .findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("Item not found: " + actualQty.getItemId()));

            item.setActualQuantity(actualQty.getActualQuantity());
        }

        // Update status
        receipt.setStatus(ReceiptStatus.CONFIRMED);
        receipt.setConfirmedBy(currentUser);
        receipt.setConfirmedAt(LocalDateTime.now());

        receipt = receiptRepository.save(receipt);

        // Update stock
        for (ReceiptItem item : receipt.getItems()) {
            if (item.getActualQuantity() > 0) {
                try {
                    // Find existing stock or it will be created by setStock
                    StockDTO existingStock = stockService.getStock(item.getProduct().getId(), receipt.getFacility().getId());

                    if (existingStock != null) {
                        // Adjust existing stock
                        stockService.adjustStock(
                                item.getProduct().getId(),
                                receipt.getFacility().getId(),
                                item.getActualQuantity()
                        );
                    } else {
                        // Create new stock
                        stockService.setStock(
                                item.getProduct().getId(),
                                receipt.getFacility().getId(),
                                item.getActualQuantity()
                        );
                    }

                    log.info("Stock updated for product {} at facility {}: +{}",
                            item.getProduct().getId(),
                            receipt.getFacility().getCode(),
                            item.getActualQuantity());
                } catch (Exception e) {
                    log.error("Failed to update stock for item {}: {}", item.getId(), e.getMessage());
                    throw new RuntimeException("Failed to update stock: " + e.getMessage(), e);
                }
            }
        }

        log.info("Receipt {} confirmed by user {}, stock updated", receipt.getDocumentNumber(), currentUser.getUsername());

        // If this receipt was auto-created from a shipment, mark shipment as DELIVERED
        if (logisticsEventProducer != null && receipt.getSourceShipment() != null) {
            logisticsEventProducer.sendShipmentDelivered(
                    receipt.getSourceShipment().getId(),
                    receipt.getSourceShipment().getDocumentNumber()
            );
            log.info("Sent DELIVERED event for source shipment {}", receipt.getSourceShipment().getDocumentNumber());
        }

        return toDTO(receipt);
    }

    /**
     * Завершить документ: CONFIRMED → COMPLETED
     */
    @Transactional
    public ReceiptDocumentDTO complete(Long id) {
        log.info("Completing receipt document {}", id);

        ReceiptDocument receipt = receiptRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Receipt not found: " + id));

        // Validate state
        if (receipt.getStatus() != ReceiptStatus.CONFIRMED) {
            throw new IllegalStateException("Only CONFIRMED receipts can be completed. Current status: " + receipt.getStatus());
        }

        // Update status
        receipt.setStatus(ReceiptStatus.COMPLETED);
        receipt = receiptRepository.save(receipt);

        log.info("Receipt {} completed", receipt.getDocumentNumber());

        return toDTO(receipt);
    }

    /**
     * Удалить документ (только DRAFT)
     */
    @Transactional
    public void delete(Long id) {
        log.info("Deleting receipt document {}", id);

        ReceiptDocument receipt = receiptRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Receipt not found: " + id));

        // Only DRAFT can be deleted
        if (receipt.getStatus() != ReceiptStatus.DRAFT) {
            throw new IllegalStateException("Only DRAFT receipts can be deleted. Current status: " + receipt.getStatus());
        }

        receiptRepository.delete(receipt);
        log.info("Receipt {} deleted", receipt.getDocumentNumber());
    }

    /**
     * Генерация номера документа
     * Формат: RCP-{facilityCode}-{YYYYMMDD}-{seq}
     * Пример: RCP-WH-C-001-20251211-001
     */
    private String generateDocumentNumber(Facility facility) {
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

    /**
     * Преобразовать Entity в DTO
     */
    private ReceiptDocumentDTO toDTO(ReceiptDocument receipt) {
        List<ReceiptItemDTO> itemDTOs = receipt.getItems().stream()
                .map(item -> ReceiptItemDTO.builder()
                        .id(item.getId())
                        .productId(item.getProduct().getId())
                        .productName(item.getProduct().getName())
                        .expectedQuantity(item.getExpectedQuantity())
                        .actualQuantity(item.getActualQuantity())
                        .build())
                .collect(Collectors.toList());

        Integer totalExpected = receipt.getItems().stream()
                .mapToInt(ReceiptItem::getExpectedQuantity)
                .sum();

        Integer totalActual = receipt.getItems().stream()
                .mapToInt(ReceiptItem::getActualQuantity)
                .sum();

        return ReceiptDocumentDTO.builder()
                .id(receipt.getId())
                .documentNumber(receipt.getDocumentNumber())
                .facilityId(receipt.getFacility().getId())
                .facilityCode(receipt.getFacility().getCode())
                .facilityName(receipt.getFacility().getName())
                .supplierName(receipt.getSupplierName())
                .sourceShipmentId(receipt.getSourceShipment() != null ? receipt.getSourceShipment().getId() : null)
                .status(receipt.getStatus())
                .notes(receipt.getNotes())
                .createdAt(receipt.getCreatedAt())
                .createdByUsername(receipt.getCreatedBy() != null ? receipt.getCreatedBy().getUsername() : null)
                .approvedAt(receipt.getApprovedAt())
                .approvedByUsername(receipt.getApprovedBy() != null ? receipt.getApprovedBy().getUsername() : null)
                .confirmedAt(receipt.getConfirmedAt())
                .confirmedByUsername(receipt.getConfirmedBy() != null ? receipt.getConfirmedBy().getUsername() : null)
                .items(itemDTOs)
                .totalExpected(totalExpected)
                .totalActual(totalActual)
                .build();
    }
}
