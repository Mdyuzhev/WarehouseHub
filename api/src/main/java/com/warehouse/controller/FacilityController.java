package com.warehouse.controller;

import com.warehouse.dto.FacilityCreateRequest;
import com.warehouse.dto.FacilityResponse;
import com.warehouse.dto.FacilityTreeNode;
import com.warehouse.dto.FacilityUpdateRequest;
import com.warehouse.model.FacilityType;
import com.warehouse.service.FacilityService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * REST контроллер для управления объектами логистической сети
 */
@RestController
@RequestMapping("/api/facilities")
@RequiredArgsConstructor
@Tag(name = "Facilities", description = "API для управления объектами логистической сети (DC, WH, PP)")
@SecurityRequirement(name = "bearerAuth")
public class FacilityController {

    private final FacilityService facilityService;

    /**
     * Получить все объекты
     */
    @GetMapping
    @Operation(summary = "Получить все объекты логистической сети")
    public ResponseEntity<List<FacilityResponse>> getAllFacilities() {
        return ResponseEntity.ok(facilityService.findAll());
    }

    /**
     * Получить иерархию объектов в виде дерева
     */
    @GetMapping("/tree")
    @Operation(summary = "Получить иерархию объектов (DC → WH → PP)")
    public ResponseEntity<List<FacilityTreeNode>> getFacilityTree() {
        return ResponseEntity.ok(facilityService.getTree());
    }

    /**
     * Получить объект по ID
     */
    @GetMapping("/{id}")
    @Operation(summary = "Получить объект по ID")
    public ResponseEntity<FacilityResponse> getFacilityById(@PathVariable Long id) {
        return ResponseEntity.ok(facilityService.findById(id));
    }

    /**
     * Получить объект по коду
     */
    @GetMapping("/code/{code}")
    @Operation(summary = "Получить объект по коду (DC-001, WH-C-001, PP-C-001-01)")
    public ResponseEntity<FacilityResponse> getFacilityByCode(@PathVariable String code) {
        return ResponseEntity.ok(facilityService.findByCode(code));
    }

    /**
     * Получить объекты по типу
     */
    @GetMapping("/type/{type}")
    @Operation(summary = "Получить объекты по типу (DC, WH, PP)")
    public ResponseEntity<List<FacilityResponse>> getFacilitiesByType(@PathVariable FacilityType type) {
        return ResponseEntity.ok(facilityService.findByType(type));
    }

    /**
     * Получить дочерние объекты
     */
    @GetMapping("/{id}/children")
    @Operation(summary = "Получить дочерние объекты (склады для РЦ, пункты выдачи для склада)")
    public ResponseEntity<List<FacilityResponse>> getFacilityChildren(@PathVariable Long id) {
        return ResponseEntity.ok(facilityService.findChildren(id));
    }

    /**
     * Создать новый объект
     * Доступно только для SUPER_USER и ADMIN
     */
    @PostMapping
    @PreAuthorize("hasAnyRole('SUPER_USER', 'ADMIN')")
    @Operation(summary = "Создать новый объект логистической сети (только SUPER_USER, ADMIN)")
    public ResponseEntity<FacilityResponse> createFacility(@Valid @RequestBody FacilityCreateRequest request) {
        FacilityResponse created = facilityService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    /**
     * Обновить объект
     * Доступно только для SUPER_USER и ADMIN
     */
    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('SUPER_USER', 'ADMIN')")
    @Operation(summary = "Обновить объект логистической сети (только SUPER_USER, ADMIN)")
    public ResponseEntity<FacilityResponse> updateFacility(
            @PathVariable Long id,
            @Valid @RequestBody FacilityUpdateRequest request) {
        FacilityResponse updated = facilityService.update(id, request);
        return ResponseEntity.ok(updated);
    }
}
