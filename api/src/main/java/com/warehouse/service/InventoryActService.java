package com.warehouse.service;

import com.warehouse.dto.*;
import com.warehouse.model.*;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.InventoryActRepository;
import com.warehouse.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Сервис для работы с актами инвентаризации
 * WH-275: Inventory Acts
 *
 * State Machine: DRAFT → COMPLETED
 * - COMPLETED: stock correction based on difference (actual - expected)
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class InventoryActService {

    private final InventoryActRepository inventoryActRepository;
    private final FacilityRepository facilityRepository;
    private final ProductRepository productRepository;
    private final StockService stockService;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");

    /**
     * Создать акт инвентаризации (DRAFT)
     */
    @Transactional
    public InventoryActDTO create(InventoryActCreateRequest request, User currentUser) {
        log.info("Creating inventory act for facility {}", request.getFacilityId());

        // Validate facility
        Facility facility = facilityRepository.findById(request.getFacilityId())
                .orElseThrow(() -> new IllegalArgumentException("Facility not found: " + request.getFacilityId()));

        // Validate items
        if (request.getItems() == null || request.getItems().isEmpty()) {
            throw new IllegalArgumentException("Inventory act must have at least one item");
        }

        // Generate document number
        String documentNumber = generateDocumentNumber(facility);

        // Create document
        InventoryAct inventoryAct = InventoryAct.builder()
                .documentNumber(documentNumber)
                .facility(facility)
                .notes(request.getNotes())
                .status(InventoryStatus.DRAFT)
                .createdBy(currentUser)
                .build();

        // Add items
        for (InventoryActCreateRequest.InventoryActItemRequest itemRequest : request.getItems()) {
            Product product = productRepository.findById(itemRequest.getProductId())
                    .orElseThrow(() -> new IllegalArgumentException("Product not found: " + itemRequest.getProductId()));

            InventoryActItem item = InventoryActItem.builder()
                    .product(product)
                    .expectedQuantity(itemRequest.getExpectedQuantity())
                    .actualQuantity(itemRequest.getActualQuantity())
                    .build();

            inventoryAct.addItem(item);
        }

        inventoryAct = inventoryActRepository.save(inventoryAct);
        log.info("Inventory act created: {}", documentNumber);

        return toDTO(inventoryAct);
    }

    /**
     * Получить акт по ID
     */
    @Transactional(readOnly = true)
    public InventoryActDTO getById(Long id) {
        InventoryAct inventoryAct = inventoryActRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Inventory act not found: " + id));
        return toDTO(inventoryAct);
    }

    /**
     * Получить все акты по facility (с пагинацией)
     */
    @Transactional(readOnly = true)
    public PageResponse<InventoryActDTO> getByFacility(Long facilityId, Pageable pageable) {
        Page<InventoryAct> page = inventoryActRepository.findByFacilityId(facilityId, pageable);
        return PageResponse.from(page.map(this::toDTO));
    }

    /**
     * Завершить акт: DRAFT → COMPLETED
     * Apply stock corrections based on differences
     */
    @Transactional
    public InventoryActDTO complete(Long id, User currentUser) {
        log.info("Completing inventory act {}", id);

        InventoryAct inventoryAct = inventoryActRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Inventory act not found: " + id));

        // Validate state
        if (inventoryAct.getStatus() != InventoryStatus.DRAFT) {
            throw new IllegalStateException("Only DRAFT inventory acts can be completed. Current status: " + inventoryAct.getStatus());
        }

        // Validate items
        if (inventoryAct.getItems().isEmpty()) {
            throw new IllegalStateException("Cannot complete inventory act without items");
        }

        // Apply stock corrections for each item
        for (InventoryActItem item : inventoryAct.getItems()) {
            int difference = item.getDifference(); // actual - expected

            if (difference != 0) {
                try {
                    // Adjust stock by difference
                    stockService.adjustStock(
                            item.getProduct().getId(),
                            inventoryAct.getFacility().getId(),
                            difference
                    );
                    log.info("Stock corrected for product {} at facility {}: {} (expected: {}, actual: {}, diff: {})",
                            item.getProduct().getId(),
                            inventoryAct.getFacility().getCode(),
                            difference > 0 ? "+" + difference : difference,
                            item.getExpectedQuantity(),
                            item.getActualQuantity(),
                            difference);
                } catch (Exception e) {
                    log.error("Failed to correct stock for item {}: {}", item.getId(), e.getMessage());
                    throw new RuntimeException("Failed to correct stock: " + e.getMessage(), e);
                }
            } else {
                log.info("No stock correction needed for product {} at facility {} (quantities match)",
                        item.getProduct().getId(),
                        inventoryAct.getFacility().getCode());
            }
        }

        // Update status
        inventoryAct.setStatus(InventoryStatus.COMPLETED);
        inventoryAct.setCompletedBy(currentUser);
        inventoryAct.setCompletedAt(LocalDateTime.now());

        inventoryAct = inventoryActRepository.save(inventoryAct);
        log.info("Inventory act {} completed, stock corrected", inventoryAct.getDocumentNumber());

        return toDTO(inventoryAct);
    }

    /**
     * Удалить акт (только DRAFT)
     */
    @Transactional
    public void delete(Long id) {
        log.info("Deleting inventory act {}", id);

        InventoryAct inventoryAct = inventoryActRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Inventory act not found: " + id));

        // Only DRAFT can be deleted
        if (inventoryAct.getStatus() != InventoryStatus.DRAFT) {
            throw new IllegalStateException("Only DRAFT inventory acts can be deleted. Current status: " + inventoryAct.getStatus());
        }

        inventoryActRepository.delete(inventoryAct);
        log.info("Inventory act {} deleted", inventoryAct.getDocumentNumber());
    }

    /**
     * Генерация номера документа
     * Формат: INV-{facilityCode}-{YYYYMMDD}-{seq}
     * Пример: INV-WH-C-001-20251211-001
     */
    private String generateDocumentNumber(Facility facility) {
        LocalDate today = LocalDate.now();
        LocalDateTime startOfDay = today.atStartOfDay();
        LocalDateTime endOfDay = today.plusDays(1).atStartOfDay();

        Long count = inventoryActRepository.countByFacilityAndDate(
                facility.getId(),
                startOfDay,
                endOfDay
        );

        int sequence = count.intValue() + 1;
        String dateStr = DATE_FORMATTER.format(today);

        return String.format("INV-%s-%s-%03d", facility.getCode(), dateStr, sequence);
    }

    /**
     * Преобразовать Entity в DTO
     */
    private InventoryActDTO toDTO(InventoryAct inventoryAct) {
        List<InventoryActItemDTO> itemDTOs = inventoryAct.getItems().stream()
                .map(item -> InventoryActItemDTO.builder()
                        .id(item.getId())
                        .productId(item.getProduct().getId())
                        .productName(item.getProduct().getName())
                        .expectedQuantity(item.getExpectedQuantity())
                        .actualQuantity(item.getActualQuantity())
                        .difference(item.getDifference())
                        .build())
                .collect(Collectors.toList());

        Integer totalExpected = inventoryAct.getItems().stream()
                .mapToInt(InventoryActItem::getExpectedQuantity)
                .sum();

        Integer totalActual = inventoryAct.getItems().stream()
                .mapToInt(InventoryActItem::getActualQuantity)
                .sum();

        Integer totalDifference = totalActual - totalExpected;

        return InventoryActDTO.builder()
                .id(inventoryAct.getId())
                .documentNumber(inventoryAct.getDocumentNumber())
                .facilityId(inventoryAct.getFacility().getId())
                .facilityCode(inventoryAct.getFacility().getCode())
                .facilityName(inventoryAct.getFacility().getName())
                .status(inventoryAct.getStatus())
                .notes(inventoryAct.getNotes())
                .createdAt(inventoryAct.getCreatedAt())
                .createdByUsername(inventoryAct.getCreatedBy() != null ? inventoryAct.getCreatedBy().getUsername() : null)
                .completedAt(inventoryAct.getCompletedAt())
                .completedByUsername(inventoryAct.getCompletedBy() != null ? inventoryAct.getCompletedBy().getUsername() : null)
                .items(itemDTOs)
                .totalExpected(totalExpected)
                .totalActual(totalActual)
                .totalDifference(totalDifference)
                .build();
    }
}
