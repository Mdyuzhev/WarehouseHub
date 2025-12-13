package com.warehouse.service;

import com.warehouse.dto.*;
import com.warehouse.model.*;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.IssueActRepository;
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
 * Сервис для работы с актами выдачи
 * WH-275: Issue Acts
 *
 * State Machine: DRAFT → COMPLETED
 * - COMPLETED: instant stock deduction (no reservation)
 * - Only for PP (pickup points)
 */
@Service
@RequiredArgsConstructor
@Slf4j
@SuppressWarnings("null")
public class IssueActService {

    private final IssueActRepository issueActRepository;
    private final FacilityRepository facilityRepository;
    private final ProductRepository productRepository;
    private final StockService stockService;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");

    /**
     * Создать акт выдачи (DRAFT)
     */
    @Transactional
    public IssueActDTO create(IssueActCreateRequest request, User currentUser) {
        log.info("Creating issue act for facility {}", request.getFacilityId());

        // Validate facility (must be PP)
        Facility facility = facilityRepository.findById(request.getFacilityId())
                .orElseThrow(() -> new IllegalArgumentException("Facility not found: " + request.getFacilityId()));

        if (facility.getType() != FacilityType.PP) {
            throw new IllegalArgumentException("Issue acts can only be created for pickup points (PP). Facility type: " + facility.getType());
        }

        // Validate items
        if (request.getItems() == null || request.getItems().isEmpty()) {
            throw new IllegalArgumentException("Issue act must have at least one item");
        }

        // Generate document number
        String documentNumber = generateDocumentNumber(facility);

        // Create document
        IssueAct issueAct = IssueAct.builder()
                .documentNumber(documentNumber)
                .facility(facility)
                .customerName(request.getCustomerName())
                .customerPhone(request.getCustomerPhone())
                .notes(request.getNotes())
                .status(IssueStatus.DRAFT)
                .createdBy(currentUser)
                .build();

        // Add items
        for (IssueActCreateRequest.IssueActItemRequest itemRequest : request.getItems()) {
            Product product = productRepository.findById(itemRequest.getProductId())
                    .orElseThrow(() -> new IllegalArgumentException("Product not found: " + itemRequest.getProductId()));

            IssueActItem item = IssueActItem.builder()
                    .product(product)
                    .quantity(itemRequest.getQuantity())
                    .build();

            issueAct.addItem(item);
        }

        issueAct = issueActRepository.save(issueAct);
        log.info("Issue act created: {}", documentNumber);

        return toDTO(issueAct);
    }

    /**
     * Получить акт по ID
     */
    @Transactional(readOnly = true)
    public IssueActDTO getById(Long id) {
        IssueAct issueAct = issueActRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Issue act not found: " + id));
        return toDTO(issueAct);
    }

    /**
     * Получить все акты по facility (с пагинацией)
     */
    @Transactional(readOnly = true)
    public PageResponse<IssueActDTO> getByFacility(Long facilityId, Pageable pageable) {
        Page<IssueAct> page = issueActRepository.findByFacilityId(facilityId, pageable);
        return PageResponse.from(page.map(this::toDTO));
    }

    /**
     * Завершить акт: DRAFT → COMPLETED
     * Instant stock deduction (no reservation)
     */
    @Transactional
    public IssueActDTO complete(Long id, User currentUser) {
        log.info("Completing issue act {}", id);

        IssueAct issueAct = issueActRepository.findByIdWithItems(id)
                .orElseThrow(() -> new IllegalArgumentException("Issue act not found: " + id));

        // Validate state
        if (issueAct.getStatus() != IssueStatus.DRAFT) {
            throw new IllegalStateException("Only DRAFT issue acts can be completed. Current status: " + issueAct.getStatus());
        }

        // Validate items
        if (issueAct.getItems().isEmpty()) {
            throw new IllegalStateException("Cannot complete issue act without items");
        }

        // Deduct stock for each item (instant, no reservation)
        for (IssueActItem item : issueAct.getItems()) {
            try {
                stockService.adjustStock(
                        item.getProduct().getId(),
                        issueAct.getFacility().getId(),
                        -item.getQuantity() // Negative for deduction
                );
                log.info("Deducted {} units of product {} from facility {}",
                        item.getQuantity(),
                        item.getProduct().getId(),
                        issueAct.getFacility().getCode());
            } catch (Exception e) {
                log.error("Failed to deduct stock for item {}: {}", item.getId(), e.getMessage());
                throw new RuntimeException("Failed to deduct stock: " + e.getMessage(), e);
            }
        }

        // Update status
        issueAct.setStatus(IssueStatus.COMPLETED);
        issueAct.setCompletedAt(LocalDateTime.now());

        issueAct = issueActRepository.save(issueAct);
        log.info("Issue act {} completed, stock deducted", issueAct.getDocumentNumber());

        return toDTO(issueAct);
    }

    /**
     * Удалить акт (только DRAFT)
     */
    @Transactional
    public void delete(Long id) {
        log.info("Deleting issue act {}", id);

        IssueAct issueAct = issueActRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Issue act not found: " + id));

        // Only DRAFT can be deleted
        if (issueAct.getStatus() != IssueStatus.DRAFT) {
            throw new IllegalStateException("Only DRAFT issue acts can be deleted. Current status: " + issueAct.getStatus());
        }

        issueActRepository.delete(issueAct);
        log.info("Issue act {} deleted", issueAct.getDocumentNumber());
    }

    /**
     * Генерация номера документа
     * Формат: ISS-{facilityCode}-{YYYYMMDD}-{seq}
     * Пример: ISS-PP-M-001-20251211-001
     */
    private String generateDocumentNumber(Facility facility) {
        LocalDate today = LocalDate.now();
        LocalDateTime startOfDay = today.atStartOfDay();
        LocalDateTime endOfDay = today.plusDays(1).atStartOfDay();

        Long count = issueActRepository.countByFacilityAndDate(
                facility.getId(),
                startOfDay,
                endOfDay
        );

        int sequence = count.intValue() + 1;
        String dateStr = DATE_FORMATTER.format(today);

        return String.format("ISS-%s-%s-%03d", facility.getCode(), dateStr, sequence);
    }

    /**
     * Преобразовать Entity в DTO
     */
    private IssueActDTO toDTO(IssueAct issueAct) {
        List<IssueActItemDTO> itemDTOs = issueAct.getItems().stream()
                .map(item -> IssueActItemDTO.builder()
                        .id(item.getId())
                        .productId(item.getProduct().getId())
                        .productName(item.getProduct().getName())
                        .quantity(item.getQuantity())
                        .build())
                .collect(Collectors.toList());

        Integer totalQuantity = issueAct.getItems().stream()
                .mapToInt(IssueActItem::getQuantity)
                .sum();

        return IssueActDTO.builder()
                .id(issueAct.getId())
                .documentNumber(issueAct.getDocumentNumber())
                .facilityId(issueAct.getFacility().getId())
                .facilityCode(issueAct.getFacility().getCode())
                .facilityName(issueAct.getFacility().getName())
                .customerName(issueAct.getCustomerName())
                .customerPhone(issueAct.getCustomerPhone())
                .status(issueAct.getStatus())
                .notes(issueAct.getNotes())
                .createdAt(issueAct.getCreatedAt())
                .createdByUsername(issueAct.getCreatedBy() != null ? issueAct.getCreatedBy().getUsername() : null)
                .completedAt(issueAct.getCompletedAt())
                .items(itemDTOs)
                .totalQuantity(totalQuantity)
                .build();
    }
}
