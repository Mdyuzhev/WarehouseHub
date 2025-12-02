package com.warehouse.repository;

import com.warehouse.model.Facility;
import com.warehouse.model.FacilityType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repository для работы с объектами логистической сети
 */
@Repository
public interface FacilityRepository extends JpaRepository<Facility, Long> {

    /**
     * Найти объект по коду
     */
    Optional<Facility> findByCode(String code);

    /**
     * Проверить существование объекта по коду
     */
    boolean existsByCode(String code);

    /**
     * Найти объекты по типу
     */
    List<Facility> findByType(FacilityType type);

    /**
     * Найти объекты по типу и статусу
     */
    List<Facility> findByTypeAndStatus(FacilityType type, String status);

    /**
     * Найти дочерние объекты по ID родителя
     */
    List<Facility> findByParentId(Long parentId);

    /**
     * Найти все активные распределительные центры (корневые объекты)
     */
    @Query("SELECT f FROM Facility f WHERE f.type = 'DC' AND f.status = 'ACTIVE' AND f.parentId IS NULL ORDER BY f.code")
    List<Facility> findAllDistributionCenters();

    /**
     * Найти склады по ID распределительного центра
     */
    @Query("SELECT f FROM Facility f WHERE f.type = 'WH' AND f.parentId = :dcId AND f.status = 'ACTIVE' ORDER BY f.code")
    List<Facility> findWarehousesByDcId(@Param("dcId") Long dcId);

    /**
     * Найти пункты выдачи по ID склада
     */
    @Query("SELECT f FROM Facility f WHERE f.type = 'PP' AND f.parentId = :whId AND f.status = 'ACTIVE' ORDER BY f.code")
    List<Facility> findPickupPointsByWarehouseId(@Param("whId") Long whId);

    /**
     * Подсчитать количество объектов по типу
     */
    long countByType(FacilityType type);

    /**
     * Найти максимальный номер DC для автогенерации кода
     * Код DC: DC-001, DC-002, ...
     */
    @Query("SELECT MAX(CAST(SUBSTRING(f.code, 4) AS int)) FROM Facility f WHERE f.type = 'DC' AND f.code LIKE 'DC-%'")
    Integer findMaxDcNumber();

    /**
     * Найти максимальный номер WH для заданного региона
     * Код WH: WH-C-001, WH-N-002, ...
     */
    @Query("SELECT MAX(CAST(SUBSTRING(f.code, LENGTH(:prefix) + 1) AS int)) FROM Facility f WHERE f.type = 'WH' AND f.code LIKE CONCAT(:prefix, '%')")
    Integer findMaxWhNumberByRegion(@Param("prefix") String prefix);

    /**
     * Найти максимальный номер PP для заданного склада
     * Код PP: PP-C-001-01, PP-N-002-03, ...
     */
    @Query("SELECT MAX(CAST(SUBSTRING(f.code, LENGTH(:prefix) + 1) AS int)) FROM Facility f WHERE f.type = 'PP' AND f.code LIKE CONCAT(:prefix, '%')")
    Integer findMaxPpNumberByWarehouse(@Param("prefix") String prefix);
}
