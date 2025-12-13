package com.warehouse.service;

import com.warehouse.dto.NotificationRequest;
import com.warehouse.model.Notification;
import com.warehouse.model.NotificationStatus;
import com.warehouse.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * Сервис для работы с уведомлениями
 */
@Service
@RequiredArgsConstructor
@Slf4j
@SuppressWarnings("null")
public class NotificationService {

    private final NotificationRepository notificationRepository;

    /**
     * Отправить уведомление (создать в БД со статусом PENDING)
     */
    @Transactional
    public Notification send(NotificationRequest request) {
        log.info("Создание уведомления: channel={}, recipient={}",
                request.getChannel(), request.getRecipient());

        Notification notification = Notification.builder()
                .channel(request.getChannel())
                .recipient(request.getRecipient())
                .subject(request.getSubject())
                .message(request.getMessage())
                .priority(request.getPriority() != null ? request.getPriority() : 5)
                .status(NotificationStatus.PENDING)
                .retryCount(0)
                .build();

        Notification saved = notificationRepository.save(notification);
        log.info("Уведомление #{} создано и добавлено в очередь", saved.getId());

        return saved;
    }

    /**
     * Найти уведомление по ID
     */
    public Optional<Notification> findById(Long id) {
        return notificationRepository.findById(id);
    }

    /**
     * Получить статистику по уведомлениям
     */
    public Map<String, Long> getStats() {
        Map<String, Long> stats = new HashMap<>();

        for (NotificationStatus status : NotificationStatus.values()) {
            long count = notificationRepository.countByStatus(status);
            stats.put(status.name(), count);
        }

        long total = notificationRepository.count();
        stats.put("TOTAL", total);

        log.debug("Статистика уведомлений: {}", stats);
        return stats;
    }

    /**
     * Сохранить уведомление
     */
    @Transactional
    public Notification save(Notification notification) {
        return notificationRepository.save(notification);
    }
}
