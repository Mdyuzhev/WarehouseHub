package com.warehouse.controller;

import com.warehouse.dto.PageResponse;
import com.warehouse.dto.ShipmentCreateRequest;
import com.warehouse.dto.ShipmentDocumentDTO;
import com.warehouse.model.User;
import com.warehouse.repository.UserRepository;
import com.warehouse.service.ShipmentDocumentService;
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
 * REST контроллер для работы с расходными накладными
 * WH-273: Shipment Documents
 */
@RestController
@RequestMapping("/api/shipments")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Shipment Documents", description = "API для работы с расходными накладными")
@SecurityRequirement(name = "bearerAuth")
public class ShipmentDocumentController {

    private final ShipmentDocumentService shipmentService;
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
     * Создать расходную накладную
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @PostMapping
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Создать расходную накладную (DRAFT)")
    public ResponseEntity<ShipmentDocumentDTO> createShipment(@Valid @RequestBody ShipmentCreateRequest request) {
        log.info("Creating shipment document from facility {}", request.getSourceFacilityId());
        try {
            User currentUser = getCurrentUser();
            ShipmentDocumentDTO created = shipmentService.create(request, currentUser);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (IllegalArgumentException e) {
            log.error("Failed to create shipment: {}", e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Получить расходную накладную по ID
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Получить расходную накладную по ID")
    public ResponseEntity<ShipmentDocumentDTO> getShipmentById(@PathVariable Long id) {
        try {
            ShipmentDocumentDTO shipment = shipmentService.getById(id);
            return ResponseEntity.ok(shipment);
        } catch (IllegalArgumentException e) {
            log.error("Shipment not found: {}", id);
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * Получить расходные накладные по объекту-источнику
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @GetMapping("/facility/{facilityId}")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Получить все расходные накладные для объекта-источника")
    public ResponseEntity<PageResponse<ShipmentDocumentDTO>> getShipmentsByFacility(
            @PathVariable Long facilityId,
            @Parameter(description = "Page number (0-based)") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by("createdAt").descending());
        PageResponse<ShipmentDocumentDTO> shipments = shipmentService.getBySourceFacility(facilityId, pageable);
        return ResponseEntity.ok(shipments);
    }

    /**
     * Утвердить расходную накладную (DRAFT → APPROVED)
     * Резервирует stock
     * Доступно: MANAGER, ADMIN
     */
    @PostMapping("/{id}/approve")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Утвердить расходную накладную (DRAFT → APPROVED), резервирует stock")
    public ResponseEntity<ShipmentDocumentDTO> approveShipment(@PathVariable Long id) {
        log.info("Approving shipment {}", id);
        try {
            User currentUser = getCurrentUser();
            ShipmentDocumentDTO approved = shipmentService.approve(id, currentUser);
            return ResponseEntity.ok(approved);
        } catch (IllegalArgumentException e) {
            log.error("Shipment not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (RuntimeException e) {
            log.error("Cannot approve shipment {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Отгрузить расходную накладную (APPROVED → SHIPPED)
     * Списывает stock
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @PostMapping("/{id}/ship")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Отгрузить расходную накладную (APPROVED → SHIPPED), списывает stock")
    public ResponseEntity<ShipmentDocumentDTO> shipShipment(@PathVariable Long id) {
        log.info("Shipping shipment {}", id);
        try {
            User currentUser = getCurrentUser();
            ShipmentDocumentDTO shipped = shipmentService.ship(id, currentUser);
            return ResponseEntity.ok(shipped);
        } catch (IllegalArgumentException e) {
            log.error("Shipment not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (RuntimeException e) {
            log.error("Cannot ship shipment {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Доставить расходную накладную (SHIPPED → DELIVERED)
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @PostMapping("/{id}/deliver")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Доставить расходную накладную (SHIPPED → DELIVERED)")
    public ResponseEntity<ShipmentDocumentDTO> deliverShipment(@PathVariable Long id) {
        log.info("Delivering shipment {}", id);
        try {
            ShipmentDocumentDTO delivered = shipmentService.deliver(id);
            return ResponseEntity.ok(delivered);
        } catch (IllegalArgumentException e) {
            log.error("Shipment not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (IllegalStateException e) {
            log.error("Cannot deliver shipment {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Отменить расходную накладную
     * Снимает резерв если был APPROVED
     * Доступно: MANAGER, ADMIN
     */
    @PostMapping("/{id}/cancel")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Отменить расходную накладную (DRAFT/APPROVED), снимает резерв")
    public ResponseEntity<Void> cancelShipment(@PathVariable Long id) {
        log.info("Cancelling shipment {}", id);
        try {
            shipmentService.cancel(id);
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            log.error("Shipment not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (RuntimeException e) {
            log.error("Cannot cancel shipment {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }
}
