package com.warehouse.controller;

import com.warehouse.dto.IssueActCreateRequest;
import com.warehouse.dto.IssueActDTO;
import com.warehouse.model.User;
import com.warehouse.repository.UserRepository;
import com.warehouse.service.IssueActService;
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
 * REST контроллер для работы с актами выдачи
 * WH-275: Issue Acts
 */
@RestController
@RequestMapping("/api/issue-acts")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Issue Acts", description = "API для работы с актами выдачи (только ПВЗ)")
@SecurityRequirement(name = "bearerAuth")
public class IssueActController {

    private final IssueActService issueActService;
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
     * Создать акт выдачи
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @PostMapping
    @PreAuthorize("hasAnyRole('EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Создать акт выдачи (DRAFT)")
    public ResponseEntity<IssueActDTO> createIssueAct(@Valid @RequestBody IssueActCreateRequest request) {
        log.info("Creating issue act for facility {}", request.getFacilityId());
        try {
            User currentUser = getCurrentUser();
            IssueActDTO created = issueActService.create(request, currentUser);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (IllegalArgumentException e) {
            log.error("Failed to create issue act: {}", e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Получить акт выдачи по ID
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Получить акт выдачи по ID")
    public ResponseEntity<IssueActDTO> getIssueActById(@PathVariable Long id) {
        try {
            IssueActDTO issueAct = issueActService.getById(id);
            return ResponseEntity.ok(issueAct);
        } catch (IllegalArgumentException e) {
            log.error("Issue act not found: {}", id);
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * Получить акты выдачи по ПВЗ
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @GetMapping("/facility/{facilityId}")
    @PreAuthorize("hasAnyRole('EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Получить все акты выдачи для ПВЗ")
    public ResponseEntity<List<IssueActDTO>> getIssueActsByFacility(@PathVariable Long facilityId) {
        List<IssueActDTO> issueActs = issueActService.getByFacility(facilityId);
        return ResponseEntity.ok(issueActs);
    }

    /**
     * Завершить акт выдачи (DRAFT → COMPLETED)
     * Instant stock deduction
     * Доступно: EMPLOYEE, MANAGER, ADMIN
     */
    @PostMapping("/{id}/complete")
    @PreAuthorize("hasAnyRole('EMPLOYEE', 'MANAGER', 'ADMIN')")
    @Operation(summary = "Завершить акт выдачи (DRAFT → COMPLETED), списывает stock")
    public ResponseEntity<IssueActDTO> completeIssueAct(@PathVariable Long id) {
        log.info("Completing issue act {}", id);
        try {
            User currentUser = getCurrentUser();
            IssueActDTO completed = issueActService.complete(id, currentUser);
            return ResponseEntity.ok(completed);
        } catch (IllegalArgumentException e) {
            log.error("Issue act not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (RuntimeException e) {
            log.error("Cannot complete issue act {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }

    /**
     * Удалить акт выдачи
     * Только DRAFT
     * Доступно: MANAGER, ADMIN
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('MANAGER', 'ADMIN')")
    @Operation(summary = "Удалить акт выдачи (только DRAFT)")
    public ResponseEntity<Void> deleteIssueAct(@PathVariable Long id) {
        log.info("Deleting issue act {}", id);
        try {
            issueActService.delete(id);
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            log.error("Issue act not found: {}", id);
            return ResponseEntity.notFound().build();
        } catch (RuntimeException e) {
            log.error("Cannot delete issue act {}: {}", id, e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }
}
