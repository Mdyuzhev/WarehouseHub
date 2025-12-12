package com.warehouse.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

/**
 * DTO для статистики по уведомлениям
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationStats {

    private Long total;
    private Long pending;
    private Long sending;
    private Long sent;
    private Long failed;
    private Long dead;

    /**
     * Создать DTO из Map со статистикой
     */
    public static NotificationStats fromMap(Map<String, Long> stats) {
        return NotificationStats.builder()
                .total(stats.getOrDefault("TOTAL", 0L))
                .pending(stats.getOrDefault("PENDING", 0L))
                .sending(stats.getOrDefault("SENDING", 0L))
                .sent(stats.getOrDefault("SENT", 0L))
                .failed(stats.getOrDefault("FAILED", 0L))
                .dead(stats.getOrDefault("DEAD", 0L))
                .build();
    }
}
