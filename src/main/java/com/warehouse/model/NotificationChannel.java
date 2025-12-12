package com.warehouse.model;

/**
 * Каналы отправки уведомлений
 */
public enum NotificationChannel {
    /**
     * Отправка через Telegram
     */
    TELEGRAM,

    /**
     * Отправка через Email
     */
    EMAIL,

    /**
     * Отправка через Webhook
     */
    WEBHOOK,

    /**
     * Отправка в память (для тестов)
     */
    IN_MEMORY
}
