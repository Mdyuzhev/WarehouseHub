package com.warehouse.service.notification;

import com.warehouse.model.Notification;
import com.warehouse.model.NotificationChannel;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * In-memory реализация NotificationSender для тестирования
 * Хранит отправленные уведомления в памяти
 */
@Component
@Slf4j
public class InMemoryNotificationSender implements NotificationSender {

    private final List<Notification> sentNotifications = Collections.synchronizedList(new ArrayList<>());

    @Override
    public boolean send(Notification notification) {
        try {
            log.info("IN_MEMORY: Отправка уведомления #{} для {}: {}",
                    notification.getId(),
                    notification.getRecipient(),
                    notification.getMessage());

            sentNotifications.add(notification);
            return true;

        } catch (Exception e) {
            log.error("IN_MEMORY: Ошибка отправки уведомления #{}: {}",
                    notification.getId(), e.getMessage(), e);
            return false;
        }
    }

    @Override
    public boolean supports(NotificationChannel channel) {
        return channel == NotificationChannel.IN_MEMORY;
    }

    @Override
    public String getChannelName() {
        return "IN_MEMORY";
    }

    /**
     * Получить список отправленных уведомлений (для тестов)
     */
    public List<Notification> getSentNotifications() {
        return new ArrayList<>(sentNotifications);
    }

    /**
     * Очистить список отправленных уведомлений (для тестов)
     */
    public void clear() {
        sentNotifications.clear();
        log.debug("IN_MEMORY: Очищен список отправленных уведомлений");
    }

    /**
     * Получить количество отправленных уведомлений
     */
    public int getCount() {
        return sentNotifications.size();
    }
}
