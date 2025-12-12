package com.warehouse.dto;

import com.warehouse.model.NotificationChannel;
import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO для создания уведомления
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationRequest {

    @NotNull(message = "Канал отправки обязателен")
    private NotificationChannel channel;

    @NotBlank(message = "Получатель обязателен")
    @Size(max = 255, message = "Получатель не должен превышать 255 символов")
    private String recipient;

    @Size(max = 255, message = "Тема не должна превышать 255 символов")
    private String subject;

    @NotBlank(message = "Сообщение обязательно")
    private String message;

    @Min(value = 1, message = "Приоритет должен быть от 1 до 10")
    @Max(value = 10, message = "Приоритет должен быть от 1 до 10")
    @Builder.Default
    private Integer priority = 5;
}
