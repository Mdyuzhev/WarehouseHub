package com.warehouse.dto;

import com.warehouse.model.Notification;
import com.warehouse.model.NotificationChannel;
import com.warehouse.model.NotificationStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * DTO для ответа с данными уведомления
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationResponse {

    private Long id;
    private NotificationChannel channel;
    private String recipient;
    private String subject;
    private String message;
    private NotificationStatus status;
    private Integer priority;
    private Integer retryCount;
    private LocalDateTime createdAt;
    private LocalDateTime sentAt;
    private String errorMessage;

    /**
     * Создать DTO из entity
     */
    public static NotificationResponse fromEntity(Notification notification) {
        return NotificationResponse.builder()
                .id(notification.getId())
                .channel(notification.getChannel())
                .recipient(notification.getRecipient())
                .subject(notification.getSubject())
                .message(notification.getMessage())
                .status(notification.getStatus())
                .priority(notification.getPriority())
                .retryCount(notification.getRetryCount())
                .createdAt(notification.getCreatedAt())
                .sentAt(notification.getSentAt())
                .errorMessage(notification.getErrorMessage())
                .build();
    }
}
