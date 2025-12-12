package com.warehouse.repository;

import com.warehouse.model.ShipmentDocument;
import com.warehouse.model.ShipmentStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Repository для работы с расходными накладными
 * WH-273: Shipment Documents
 */
@Repository
public interface ShipmentDocumentRepository extends JpaRepository<ShipmentDocument, Long> {

    /**
     * Найти документы по объекту-источнику
     */
    List<ShipmentDocument> findBySourceFacilityId(Long sourceFacilityId);

    /**
     * Найти документы по объекту-получателю
     */
    List<ShipmentDocument> findByDestinationFacilityId(Long destinationFacilityId);

    /**
     * Найти документы по объекту-источнику и статусу
     */
    List<ShipmentDocument> findBySourceFacilityIdAndStatus(Long sourceFacilityId, ShipmentStatus status);

    /**
     * Найти документ по номеру
     */
    Optional<ShipmentDocument> findByDocumentNumber(String documentNumber);

    /**
     * Найти документ с позициями (JOIN FETCH для избежания N+1)
     */
    @Query("SELECT s FROM ShipmentDocument s LEFT JOIN FETCH s.items WHERE s.id = :id")
    Optional<ShipmentDocument> findByIdWithItems(@Param("id") Long id);

    /**
     * Подсчитать количество документов за период для генерации номера
     */
    @Query("SELECT COUNT(s) FROM ShipmentDocument s WHERE s.sourceFacility.id = :facilityId " +
           "AND s.createdAt >= :startDate AND s.createdAt < :endDate")
    Long countByFacilityAndDate(@Param("facilityId") Long facilityId,
                                 @Param("startDate") LocalDateTime startDate,
                                 @Param("endDate") LocalDateTime endDate);

    /**
     * Найти документы по статусу
     */
    List<ShipmentDocument> findByStatus(ShipmentStatus status);

    /**
     * Найти документы, созданные пользователем
     */
    List<ShipmentDocument> findByCreatedById(Long userId);
}
