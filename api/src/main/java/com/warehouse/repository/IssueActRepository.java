package com.warehouse.repository;

import com.warehouse.model.IssueAct;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Repository для актов выдачи
 * WH-275: Issue Acts
 */
@Repository
public interface IssueActRepository extends JpaRepository<IssueAct, Long> {

    /**
     * Найти акт с позициями
     */
    @Query("SELECT ia FROM IssueAct ia LEFT JOIN FETCH ia.items WHERE ia.id = :id")
    Optional<IssueAct> findByIdWithItems(@Param("id") Long id);

    /**
     * Найти все акты по facility
     */
    List<IssueAct> findByFacilityId(Long facilityId);

    /**
     * Найти все акты по facility (с пагинацией)
     */
    Page<IssueAct> findByFacilityId(Long facilityId, Pageable pageable);

    /**
     * Подсчитать акты по facility за период (для генерации номера)
     */
    @Query("SELECT COUNT(ia) FROM IssueAct ia WHERE ia.facility.id = :facilityId " +
           "AND ia.createdAt >= :startDate AND ia.createdAt < :endDate")
    Long countByFacilityAndDate(@Param("facilityId") Long facilityId,
                                @Param("startDate") LocalDateTime startDate,
                                @Param("endDate") LocalDateTime endDate);
}
