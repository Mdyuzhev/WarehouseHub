package com.warehouse.controller;

import com.warehouse.dto.NotificationRequest;
import com.warehouse.dto.NotificationResponse;
import com.warehouse.dto.NotificationStats;
import com.warehouse.model.Notification;
import com.warehouse.service.NotificationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * REST API для управления уведомлениями
 */
@RestController
@RequestMapping("/api/notifications")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Notifications", description = "Notification Service API")
public class NotificationController {

    private final NotificationService notificationService;

    /**
     * Создать новое уведомление
     */
    @PostMapping
    @Operation(summary = "Create notification", description = "Creates a new notification and adds it to the processing queue")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "201", description = "Notification created successfully",
                    content = @Content(schema = @Schema(implementation = NotificationResponse.class))),
            @ApiResponse(responseCode = "400", description = "Invalid input data",
                    content = @Content)
    })
    public ResponseEntity<NotificationResponse> createNotification(
            @Valid @RequestBody NotificationRequest request) {

        log.info("API: Создание уведомления channel={}, recipient={}",
                request.getChannel(), request.getRecipient());

        Notification notification = notificationService.send(request);
        NotificationResponse response = NotificationResponse.fromEntity(notification);

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /**
     * Получить уведомление по ID
     */
    @GetMapping("/{id}")
    @Operation(summary = "Get notification by ID", description = "Returns a single notification by its ID")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Notification found",
                    content = @Content(schema = @Schema(implementation = NotificationResponse.class))),
            @ApiResponse(responseCode = "404", description = "Notification not found")
    })
    public ResponseEntity<NotificationResponse> getNotificationById(@PathVariable Long id) {
        log.debug("API: Запрос уведомления #{}", id);

        return notificationService.findById(id)
                .map(NotificationResponse::fromEntity)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Получить статистику по уведомлениям
     */
    @GetMapping("/stats")
    @Operation(summary = "Get notification statistics", description = "Returns statistics about notifications by status")
    @ApiResponse(responseCode = "200", description = "Statistics retrieved successfully",
            content = @Content(schema = @Schema(implementation = NotificationStats.class)))
    public ResponseEntity<NotificationStats> getStats() {
        log.debug("API: Запрос статистики уведомлений");

        Map<String, Long> stats = notificationService.getStats();
        NotificationStats response = NotificationStats.fromMap(stats);

        return ResponseEntity.ok(response);
    }
}
