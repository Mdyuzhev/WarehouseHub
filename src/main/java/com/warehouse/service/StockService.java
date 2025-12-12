package com.warehouse.service;

import com.warehouse.dto.StockDTO;
import com.warehouse.model.Facility;
import com.warehouse.model.Product;
import com.warehouse.model.Stock;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.ProductRepository;
import com.warehouse.repository.StockRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Сервис для управления остатками товаров на объектах
 * WH-270: Product/Stock Separation
 */
@Service
@Slf4j
public class StockService {

    private final StockRepository stockRepository;
    private final ProductRepository productRepository;
    private final FacilityRepository facilityRepository;
    private final KafkaTemplate<String, String> kafkaTemplate;

    public StockService(StockRepository stockRepository,
                        ProductRepository productRepository,
                        FacilityRepository facilityRepository,
                        @Autowired(required = false) KafkaTemplate<String, String> kafkaTemplate) {
        this.stockRepository = stockRepository;
        this.productRepository = productRepository;
        this.facilityRepository = facilityRepository;
        this.kafkaTemplate = kafkaTemplate;
    }

    /**
     * Отправить событие изменения остатка в Kafka (WH-298)
     */
    private void sendStockEvent(String action, Stock stock, Integer delta) {
        if (kafkaTemplate == null) return;

        try {
            String event = String.format(
                "{\"type\":\"STOCK_%s\",\"productId\":%d,\"facilityId\":%d,\"facilityCode\":\"%s\"," +
                "\"quantity\":%d,\"delta\":%d,\"timestamp\":\"%s\"}",
                action, stock.getProduct().getId(), stock.getFacility().getId(),
                stock.getFacility().getCode(), stock.getQuantity(),
                delta != null ? delta : 0, Instant.now()
            );
            kafkaTemplate.send("warehouse.audit", event);
            log.debug("Stock event sent: {}", event);
        } catch (Exception e) {
            log.warn("Failed to send stock event: {}", e.getMessage());
        }
    }

    /**
     * Получить все остатки на объекте
     */
    public List<StockDTO> getStockByFacility(Long facilityId) {
        return stockRepository.findByFacilityIdAndQuantityGreaterThan(facilityId, 0)
                .stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    /**
     * Получить остатки товара на всех объектах
     */
    public List<StockDTO> getStockByProduct(Long productId) {
        return stockRepository.findByProductId(productId)
                .stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    /**
     * Получить конкретный остаток
     */
    public StockDTO getStock(Long productId, Long facilityId) {
        return stockRepository.findByProductIdAndFacilityId(productId, facilityId)
                .map(this::toDTO)
                .orElse(null);
    }

    /**
     * Установить остаток (создать или обновить)
     */
    @Transactional
    public StockDTO setStock(Long productId, Long facilityId, Integer quantity) {
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new RuntimeException("Product not found: " + productId));
        Facility facility = facilityRepository.findById(facilityId)
                .orElseThrow(() -> new RuntimeException("Facility not found: " + facilityId));

        Stock stock = stockRepository.findByProductIdAndFacilityId(productId, facilityId)
                .orElse(Stock.builder()
                        .product(product)
                        .facility(facility)
                        .quantity(0)
                        .reserved(0)
                        .build());

        int oldQuantity = stock.getQuantity();
        stock.setQuantity(quantity);
        stock = stockRepository.save(stock);

        log.info("Stock updated: product={}, facility={}, quantity={}",
                productId, facility.getCode(), quantity);
        sendStockEvent("UPDATE", stock, quantity - oldQuantity);

        return toDTO(stock);
    }

    /**
     * Изменить остаток (прибавить или отнять)
     */
    @Transactional
    public StockDTO adjustStock(Long productId, Long facilityId, Integer delta) {
        Stock stock = stockRepository.findByProductIdAndFacilityId(productId, facilityId)
                .orElseThrow(() -> new RuntimeException(
                        "Stock not found for product " + productId + " at facility " + facilityId));

        int newQuantity = stock.getQuantity() + delta;
        if (newQuantity < 0) {
            throw new RuntimeException("Cannot reduce stock below zero. Current: " +
                    stock.getQuantity() + ", delta: " + delta);
        }
        if (newQuantity < stock.getReserved()) {
            throw new RuntimeException("Cannot reduce stock below reserved. Reserved: " +
                    stock.getReserved() + ", new quantity: " + newQuantity);
        }

        stock.setQuantity(newQuantity);
        stock = stockRepository.save(stock);

        log.info("Stock adjusted: product={}, facility={}, delta={}, newQuantity={}",
                productId, stock.getFacility().getCode(), delta, newQuantity);
        sendStockEvent("ADJUST", stock, delta);

        return toDTO(stock);
    }

    /**
     * Зарезервировать товар
     */
    @Transactional
    public StockDTO reserve(Long productId, Long facilityId, Integer amount) {
        Stock stock = stockRepository.findByProductIdAndFacilityId(productId, facilityId)
                .orElseThrow(() -> new RuntimeException(
                        "Stock not found for product " + productId + " at facility " + facilityId));

        if (stock.getAvailable() < amount) {
            throw new RuntimeException("Not enough available stock. Available: " +
                    stock.getAvailable() + ", requested: " + amount);
        }

        stock.setReserved(stock.getReserved() + amount);
        stock = stockRepository.save(stock);

        log.info("Stock reserved: product={}, facility={}, amount={}, newReserved={}",
                productId, stock.getFacility().getCode(), amount, stock.getReserved());
        sendStockEvent("RESERVE", stock, amount);

        return toDTO(stock);
    }

    /**
     * Снять резерв (при отмене или подтверждении отгрузки)
     */
    @Transactional
    public StockDTO releaseReservation(Long productId, Long facilityId, Integer amount, boolean shipped) {
        Stock stock = stockRepository.findByProductIdAndFacilityId(productId, facilityId)
                .orElseThrow(() -> new RuntimeException(
                        "Stock not found for product " + productId + " at facility " + facilityId));

        if (stock.getReserved() < amount) {
            throw new RuntimeException("Cannot release more than reserved. Reserved: " +
                    stock.getReserved() + ", release: " + amount);
        }

        stock.setReserved(stock.getReserved() - amount);
        if (shipped) {
            // Если отгружено — уменьшаем quantity
            stock.setQuantity(stock.getQuantity() - amount);
        }
        stock = stockRepository.save(stock);

        log.info("Reservation released: product={}, facility={}, amount={}, shipped={}",
                productId, stock.getFacility().getCode(), amount, shipped);
        sendStockEvent(shipped ? "SHIP" : "RELEASE", stock, -amount);

        return toDTO(stock);
    }

    /**
     * Получить общий остаток товара по всем объектам
     */
    public Integer getTotalStock(Long productId) {
        return stockRepository.getTotalQuantityByProductId(productId);
    }

    /**
     * Товары с низким остатком
     */
    public List<StockDTO> getLowStock(Long facilityId, Integer threshold) {
        return stockRepository.findLowStockByFacility(facilityId, threshold)
                .stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    private StockDTO toDTO(Stock stock) {
        return StockDTO.builder()
                .id(stock.getId())
                .productId(stock.getProduct().getId())
                .productName(stock.getProduct().getName())
                .facilityId(stock.getFacility().getId())
                .facilityCode(stock.getFacility().getCode())
                .facilityName(stock.getFacility().getName())
                .quantity(stock.getQuantity())
                .reserved(stock.getReserved())
                .available(stock.getAvailable())
                .build();
    }
}
