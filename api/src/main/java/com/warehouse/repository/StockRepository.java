package com.warehouse.repository;

import com.warehouse.model.Stock;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repository для работы с остатками товаров
 * WH-270: Product/Stock Separation
 */
@Repository
public interface StockRepository extends JpaRepository<Stock, Long> {

    // Найти остаток товара на объекте
    Optional<Stock> findByProductIdAndFacilityId(Long productId, Long facilityId);

    // Все остатки товара (на всех объектах)
    List<Stock> findByProductId(Long productId);
    Page<Stock> findByProductId(Long productId, Pageable pageable);

    // Все остатки на объекте
    List<Stock> findByFacilityId(Long facilityId);

    // Остатки на объекте где quantity > 0
    List<Stock> findByFacilityIdAndQuantityGreaterThan(Long facilityId, Integer minQuantity);
    Page<Stock> findByFacilityIdAndQuantityGreaterThan(Long facilityId, Integer minQuantity, Pageable pageable);

    // Суммарный остаток товара по всем объектам
    @Query("SELECT COALESCE(SUM(s.quantity), 0) FROM Stock s WHERE s.product.id = :productId")
    Integer getTotalQuantityByProductId(@Param("productId") Long productId);

    // Суммарный остаток на объекте
    @Query("SELECT COALESCE(SUM(s.quantity), 0) FROM Stock s WHERE s.facility.id = :facilityId")
    Integer getTotalQuantityByFacilityId(@Param("facilityId") Long facilityId);

    // Товары с низким остатком на объекте
    @Query("SELECT s FROM Stock s WHERE s.facility.id = :facilityId AND s.quantity < :threshold")
    List<Stock> findLowStockByFacility(@Param("facilityId") Long facilityId, @Param("threshold") Integer threshold);

    @Query("SELECT s FROM Stock s WHERE s.facility.id = :facilityId AND s.quantity < :threshold")
    Page<Stock> findLowStockByFacility(@Param("facilityId") Long facilityId, @Param("threshold") Integer threshold, Pageable pageable);
}
