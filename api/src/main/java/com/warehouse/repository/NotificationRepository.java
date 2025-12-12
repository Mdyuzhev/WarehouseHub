package com.warehouse.repository;

import com.warehouse.model.Notification;
import com.warehouse.model.NotificationStatus;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Repository для работы с уведомлениями
 */
@Repository
public interface NotificationRepository extends JpaRepository<Notification, Long> {

    /**
     * Найти уведомления по статусу
     */
    List<Notification> findByStatus(NotificationStatus status);

    /**
     * Найти уведомления по получателю
     */
    List<Notification> findByRecipient(String recipient);

    /**
     * Найти pending уведомления, отсортированные по приоритету (desc) и времени создания (asc)
     * Используется для обработки очереди
     */
    @Query("SELECT n FROM Notification n WHERE n.status = 'PENDING' ORDER BY n.priority DESC, n.createdAt ASC")
    List<Notification> findPendingOrderByPriority(Pageable pageable);

    /**
     * Подсчитать количество уведомлений по статусу
     */
    long countByStatus(NotificationStatus status);
}
