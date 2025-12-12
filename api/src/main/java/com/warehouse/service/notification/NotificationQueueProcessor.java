package com.warehouse.service.notification;

import com.warehouse.model.Notification;
import com.warehouse.model.NotificationStatus;
import com.warehouse.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Процессор очереди уведомлений
 * Периодически обрабатывает PENDING уведомления
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class NotificationQueueProcessor {

    private static final int MAX_RETRIES = 3;
    private static final int BATCH_SIZE = 50;

    private final NotificationRepository notificationRepository;
    private final List<NotificationSender> senders;

    /**
     * Обработка очереди уведомлений каждые 5 секунд
     */
    @Scheduled(fixedDelay = 5000)
    public void processQueue() {
        try {
            Pageable pageable = PageRequest.of(0, BATCH_SIZE);
            List<Notification> pendingNotifications = notificationRepository.findPendingOrderByPriority(pageable);

            if (pendingNotifications.isEmpty()) {
                log.trace("Очередь уведомлений пуста");
                return;
            }

            log.info("Обработка {} уведомлений из очереди", pendingNotifications.size());

            for (Notification notification : pendingNotifications) {
                processNotification(notification);
            }

        } catch (Exception e) {
            log.error("Ошибка обработки очереди уведомлений: {}", e.getMessage(), e);
        }
    }

    /**
     * Обработать одно уведомление
     */
    @Transactional
    protected void processNotification(Notification notification) {
        try {
            log.debug("Обработка уведомления #{}, попытка {}/{}",
                    notification.getId(), notification.getRetryCount() + 1, MAX_RETRIES);

            // Найти подходящий sender
            NotificationSender sender = findSender(notification);
            if (sender == null) {
                markAsDead(notification, "Sender для канала " + notification.getChannel() + " не найден");
                return;
            }

            // Установить статус SENDING
            notification.setStatus(NotificationStatus.SENDING);
            notificationRepository.save(notification);

            // Попытка отправки
            boolean success = sender.send(notification);

            if (success) {
                markAsSent(notification);
            } else {
                handleFailure(notification, "Sender вернул false");
            }

        } catch (Exception e) {
            log.error("Ошибка обработки уведомления #{}: {}",
                    notification.getId(), e.getMessage(), e);
            handleFailure(notification, e.getMessage());
        }
    }

    /**
     * Найти sender для данного канала
     */
    private NotificationSender findSender(Notification notification) {
        return senders.stream()
                .filter(sender -> sender.supports(notification.getChannel()))
                .findFirst()
                .orElse(null);
    }

    /**
     * Пометить уведомление как успешно отправленное
     */
    private void markAsSent(Notification notification) {
        notification.setStatus(NotificationStatus.SENT);
        notification.setSentAt(LocalDateTime.now());
        notification.setErrorMessage(null);
        notificationRepository.save(notification);

        log.info("Уведомление #{} успешно отправлено через {}",
                notification.getId(), notification.getChannel());
    }

    /**
     * Обработать ошибку отправки
     */
    private void handleFailure(Notification notification, String errorMessage) {
        int retryCount = notification.getRetryCount();

        if (retryCount >= MAX_RETRIES) {
            markAsDead(notification, "Превышен лимит повторов: " + errorMessage);
        } else {
            notification.setStatus(NotificationStatus.FAILED);
            notification.setRetryCount(retryCount + 1);
            notification.setErrorMessage(truncateError(errorMessage));
            notificationRepository.save(notification);

            log.warn("Уведомление #{} не удалось отправить (попытка {}/{}): {}",
                    notification.getId(), retryCount + 1, MAX_RETRIES, errorMessage);

            // Вернуть в PENDING для следующей попытки
            notification.setStatus(NotificationStatus.PENDING);
            notificationRepository.save(notification);
        }
    }

    /**
     * Пометить уведомление как финально проваленное
     */
    private void markAsDead(Notification notification, String errorMessage) {
        notification.setStatus(NotificationStatus.DEAD);
        notification.setErrorMessage(truncateError(errorMessage));
        notificationRepository.save(notification);

        log.error("Уведомление #{} помечено как DEAD: {}",
                notification.getId(), errorMessage);
    }

    /**
     * Обрезать сообщение об ошибке до 1000 символов
     */
    private String truncateError(String error) {
        if (error == null) {
            return null;
        }
        return error.length() > 1000 ? error.substring(0, 997) + "..." : error;
    }
}
