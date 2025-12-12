package com.warehouse.controller;

import com.warehouse.dto.InventoryActCreateRequest;
import com.warehouse.dto.InventoryActDTO;
import com.warehouse.model.User;
import com.warehouse.repository.UserRepository;
import com.warehouse.service.InventoryActService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * REST контроллер для работы с актами инвентаризации
 * WH-275: Inventory Acts
 */
@RestController
@RequestMapping("/api/inventory-acts")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Inventory Acts", description = "API для работы с актами инвентаризации")
@SecurityRequirement(name = "bearerAuth")
public class InventoryActController {

    private final InventoryActService inventoryActService;
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
     * Создать акт инвентаризации
     * Доступно: MANAGER, ADMIN
     */
    @PostMapping
    @PreAuthorize("hasAnyRole('SUPER_USER', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Создать акт инвентаризации (DRAFT)")
    public ResponseEntity<InventoryActDTO> createInventoryAct(@Valid @RequestBody InventoryActCreateRequest request) {
        log.info("Creating inventory act for facility {}", request.getFacilityId());
        try {
            User currentUser = getCurrentUser();
            InventoryActDTO created = inventoryActService.create(request, currentUser);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (IllegalArgumentException e) {
            log.error("Failed to create inventory act: {}", e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Получить акт инвентаризации по ID
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Получить акт инвентаризации по ID")
    public ResponseEntity<InventoryActDTO> getInventoryActById(@PathVariable Long id) {
        try {
            InventoryActDTO inventoryAct = inventoryActService.getById(id);
            return ResponseEntity.ok(inventoryAct);
        } catch (IllegalArgumentException e) {
            log.error("Inventory act not found: {}", id);
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * Получить акты инвентаризации по складу
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @GetMapping("/facility/{facilityId}")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Получить все акты инвентаризации для склада")
    public ResponseEntity<List<InventoryActDTO>> getInventoryActsByFacility(@PathVariable Long facilityId) {
        List<InventoryActDTO> inventoryActs = inventoryActService.getByFacility(facilityId);
        return ResponseEntity.ok(inventoryActs);
    }

    /**
     * Завершить акт инвентаризации (DRAFT → COMPLETED)
     * Apply stock corrections
     * Доступно: MANAGER, ADMIN
     */
    @PostMapping("/{id}/complete")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Завершить акт инвентаризации (DRAFT → COMPLETED), корректирует остатки")
    public ResponseEntity<InventoryActDTO> completeInventoryAct(@PathVariable Long id) {
        log.info("Completing inventory act {}", id);
        try {
            User currentUser = getCurrentUser();
            InventoryActDTO completed = inventoryActService.complete(id, currentUser);
            return ResponseEntity.ok(completed);
        } catch (IllegalArgumentException e) {
            log.error("Inventory act not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (RuntimeException e) {
            log.error("Cannot complete inventory act {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Удалить акт инвентаризации
     * Только DRAFT
     * Доступно: MANAGER, ADMIN
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Удалить акт инвентаризации (только DRAFT)")
    public ResponseEntity<Void> deleteInventoryAct(@PathVariable Long id) {
        log.info("Deleting inventory act {}", id);
        try {
            inventoryActService.delete(id);
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            log.error("Inventory act not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (RuntimeException e) {
            log.error("Cannot delete inventory act {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }
}
