package com.warehouse.controller;

import com.warehouse.dto.PageResponse;
import com.warehouse.dto.ReceiptConfirmRequest;
import com.warehouse.dto.ReceiptCreateRequest;
import com.warehouse.dto.ReceiptDocumentDTO;
import com.warehouse.model.User;
import com.warehouse.repository.UserRepository;
import com.warehouse.service.ReceiptDocumentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

/**
 * REST контроллер для работы с приходными накладными
 * WH-272: Receipt Documents
 */
@RestController
@RequestMapping("/api/receipts")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Receipt Documents", description = "API для работы с приходными накладными")
@SecurityRequirement(name = "bearerAuth")
public class ReceiptDocumentController {

    private final ReceiptDocumentService receiptService;
    private final UserRepository userRepository;

    /**
     * Получить текущего пользователя
     */
    private User getCurrentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        String username = auth != null ? auth.getName() : null;
        if (username == null) {
            throw new IllegalStateException("User not authenticated");
        }
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new IllegalStateException("User not found: " + username));
    }

    /**
     * Создать приходную накладную
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @PostMapping
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Создать приходную накладную (DRAFT)")
    public ResponseEntity<ReceiptDocumentDTO> createReceipt(@Valid @RequestBody ReceiptCreateRequest request) {
        log.info("Creating receipt document for facility {}", request.getFacilityId());
        try {
            User currentUser = getCurrentUser();
            ReceiptDocumentDTO created = receiptService.create(request, currentUser);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (IllegalArgumentException e) {
            log.error("Failed to create receipt: {}", e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Получить приходную накладную по ID
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Получить приходную накладную по ID")
    public ResponseEntity<ReceiptDocumentDTO> getReceiptById(@PathVariable Long id) {
        try {
            ReceiptDocumentDTO receipt = receiptService.getById(id);
            return ResponseEntity.ok(receipt);
        } catch (IllegalArgumentException e) {
            log.error("Receipt not found: {}", id);
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * Получить приходные накладные по объекту
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @GetMapping("/facility/{facilityId}")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Получить все приходные накладные для объекта")
    public ResponseEntity<PageResponse<ReceiptDocumentDTO>> getReceiptsByFacility(
            @PathVariable Long facilityId,
            @Parameter(description = "Page number (0-based)") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by("createdAt").descending());
        PageResponse<ReceiptDocumentDTO> receipts = receiptService.getByFacility(facilityId, pageable);
        return ResponseEntity.ok(receipts);
    }

    /**
     * Утвердить приходную накладную (DRAFT → APPROVED)
     * Доступно: MANAGER, ADMIN
     */
    @PostMapping("/{id}/approve")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Утвердить приходную накладную (DRAFT → APPROVED)")
    public ResponseEntity<ReceiptDocumentDTO> approveReceipt(@PathVariable Long id) {
        log.info("Approving receipt {}", id);
        try {
            User currentUser = getCurrentUser();
            ReceiptDocumentDTO approved = receiptService.approve(id, currentUser);
            return ResponseEntity.ok(approved);
        } catch (IllegalArgumentException e) {
            log.error("Receipt not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (IllegalStateException e) {
            log.error("Cannot approve receipt {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Подтвердить приходную накладную (APPROVED → CONFIRMED)
     * Обновляет stock на основе actualQuantity
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @PostMapping("/{id}/confirm")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Подтвердить приходную накладную (APPROVED → CONFIRMED), обновляет stock")
    public ResponseEntity<ReceiptDocumentDTO> confirmReceipt(
            @PathVariable Long id,
            @Valid @RequestBody ReceiptConfirmRequest request) {
        log.info("Confirming receipt {}", id);
        try {
            User currentUser = getCurrentUser();
            ReceiptDocumentDTO confirmed = receiptService.confirm(id, request, currentUser);
            return ResponseEntity.ok(confirmed);
        } catch (IllegalArgumentException e) {
            log.error("Receipt or item not found: {}", e.getMessage());
            return ResponseEntity.badRequest().build();
        } catch (IllegalStateException e) {
            log.error("Cannot confirm receipt {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        } catch (RuntimeException e) {
            log.error("Failed to update stock for receipt {}: {}", id, e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * Завершить приходную накладную (CONFIRMED → COMPLETED)
     * Доступно: MANAGER, ADMIN
     */
    @PostMapping("/{id}/complete")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Завершить приходную накладную (CONFIRMED → COMPLETED)")
    public ResponseEntity<ReceiptDocumentDTO> completeReceipt(@PathVariable Long id) {
        log.info("Completing receipt {}", id);
        try {
            ReceiptDocumentDTO completed = receiptService.complete(id);
            return ResponseEntity.ok(completed);
        } catch (IllegalArgumentException e) {
            log.error("Receipt not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (IllegalStateException e) {
            log.error("Cannot complete receipt {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Удалить приходную накладную (только DRAFT)
     * Доступно: MANAGER, ADMIN
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Удалить приходную накладную (только DRAFT)")
    public ResponseEntity<Void> deleteReceipt(@PathVariable Long id) {
        log.info("Deleting receipt {}", id);
        try {
            receiptService.delete(id);
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            log.error("Receipt not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (IllegalStateException e) {
            log.error("Cannot delete receipt {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }
}
