package com.warehouse.repository;

import com.warehouse.model.ReceiptDocument;
import com.warehouse.model.ReceiptStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Repository для работы с приходными накладными
 * WH-272: Receipt Documents
 */
@Repository
public interface ReceiptDocumentRepository extends JpaRepository<ReceiptDocument, Long> {

    /**
     * Найти документы по объекту
     */
    List<ReceiptDocument> findByFacilityId(Long facilityId);

    /**
     * Найти документы по объекту и статусу
     */
    List<ReceiptDocument> findByFacilityIdAndStatus(Long facilityId, ReceiptStatus status);

    /**
     * Найти документ по номеру
     */
    Optional<ReceiptDocument> findByDocumentNumber(String documentNumber);

    /**
     * Найти документ с позициями (JOIN FETCH для избежания N+1)
     */
    @Query("SELECT r FROM ReceiptDocument r LEFT JOIN FETCH r.items WHERE r.id = :id")
    Optional<ReceiptDocument> findByIdWithItems(@Param("id") Long id);

    /**
     * Подсчитать количество документов за период для генерации номера
     * Используется для sequence в document_number
     */
    @Query("SELECT COUNT(r) FROM ReceiptDocument r WHERE r.facility.id = :facilityId " +
           "AND r.createdAt >= :startDate AND r.createdAt < :endDate")
    Long countByFacilityAndDate(@Param("facilityId") Long facilityId,
                                 @Param("startDate") LocalDateTime startDate,
                                 @Param("endDate") LocalDateTime endDate);

    /**
     * Найти документы по статусу
     */
    List<ReceiptDocument> findByStatus(ReceiptStatus status);

    /**
     * Найти документы, созданные пользователем
     */
    List<ReceiptDocument> findByCreatedById(Long userId);
}
