package com.warehouse.service;

import com.warehouse.dto.StockDTO;
import com.warehouse.model.Facility;
import com.warehouse.model.FacilityType;
import com.warehouse.model.Product;
import com.warehouse.model.Stock;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.ProductRepository;
import com.warehouse.repository.StockRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit тесты для StockService
 * WH-296: Stock Service Unit Tests
 */
@ExtendWith(MockitoExtension.class)
class StockServiceTest {

    @Mock
    private StockRepository stockRepository;

    @Mock
    private ProductRepository productRepository;

    @Mock
    private FacilityRepository facilityRepository;

    @InjectMocks
    private StockService stockService;

    private Product testProduct;
    private Facility testFacility;
    private Stock testStock;

    @BeforeEach
    void setUp() {
        testProduct = new Product();
        testProduct.setId(1L);
        testProduct.setName("Test Product");
        testProduct.setQuantity(100);
        testProduct.setPrice(99.99);

        testFacility = Facility.builder()
                .id(1L)
                .code("WH-MSK-001")
                .name("Moscow Warehouse")
                .type(FacilityType.WH)
                .status("ACTIVE")
                .build();

        testStock = Stock.builder()
                .id(1L)
                .product(testProduct)
                .facility(testFacility)
                .quantity(100)
                .reserved(10)
                .build();
    }

    @Test
    void getStock_shouldReturnStockDTO() {
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L))
                .thenReturn(Optional.of(testStock));

        StockDTO result = stockService.getStock(1L, 1L);

        assertNotNull(result);
        assertEquals(100, result.getQuantity());
        assertEquals(10, result.getReserved());
        assertEquals(90, result.getAvailable());
    }

    @Test
    void getStock_shouldReturnNullWhenNotFound() {
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L))
                .thenReturn(Optional.empty());

        StockDTO result = stockService.getStock(1L, 1L);

        assertNull(result);
    }

    @Test
    void setStock_shouldCreateNewStock() {
        when(productRepository.findById(1L)).thenReturn(Optional.of(testProduct));
        when(facilityRepository.findById(1L)).thenReturn(Optional.of(testFacility));
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L)).thenReturn(Optional.empty());
        when(stockRepository.save(any(Stock.class))).thenAnswer(inv -> {
            Stock s = inv.getArgument(0);
            s.setId(1L);
            return s;
        });

        StockDTO result = stockService.setStock(1L, 1L, 50);

        assertNotNull(result);
        assertEquals(50, result.getQuantity());
        verify(stockRepository).save(any(Stock.class));
    }

    @Test
    void setStock_shouldUpdateExistingStock() {
        when(productRepository.findById(1L)).thenReturn(Optional.of(testProduct));
        when(facilityRepository.findById(1L)).thenReturn(Optional.of(testFacility));
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L)).thenReturn(Optional.of(testStock));
        when(stockRepository.save(any(Stock.class))).thenReturn(testStock);

        StockDTO result = stockService.setStock(1L, 1L, 200);

        assertEquals(200, testStock.getQuantity());
        verify(stockRepository).save(testStock);
    }

    @Test
    void adjustStock_shouldIncreaseQuantity() {
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L))
                .thenReturn(Optional.of(testStock));
        when(stockRepository.save(any(Stock.class))).thenReturn(testStock);

        stockService.adjustStock(1L, 1L, 20);

        assertEquals(120, testStock.getQuantity());
    }

    @Test
    void adjustStock_shouldDecreaseQuantity() {
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L))
                .thenReturn(Optional.of(testStock));
        when(stockRepository.save(any(Stock.class))).thenReturn(testStock);

        stockService.adjustStock(1L, 1L, -50);

        assertEquals(50, testStock.getQuantity());
    }

    @Test
    void adjustStock_shouldThrowWhenBelowZero() {
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L))
                .thenReturn(Optional.of(testStock));

        assertThrows(RuntimeException.class, () ->
                stockService.adjustStock(1L, 1L, -200));
    }

    @Test
    void adjustStock_shouldThrowWhenBelowReserved() {
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L))
                .thenReturn(Optional.of(testStock));

        // quantity=100, reserved=10, попытка уменьшить на 95 -> новое значение 5 < reserved 10
        assertThrows(RuntimeException.class, () ->
                stockService.adjustStock(1L, 1L, -95));
    }

    @Test
    void reserve_shouldIncreaseReserved() {
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L))
                .thenReturn(Optional.of(testStock));
        when(stockRepository.save(any(Stock.class))).thenReturn(testStock);

        stockService.reserve(1L, 1L, 30);

        assertEquals(40, testStock.getReserved()); // было 10 + 30
    }

    @Test
    void reserve_shouldThrowWhenNotEnoughAvailable() {
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L))
                .thenReturn(Optional.of(testStock));

        // available = 100 - 10 = 90
        assertThrows(RuntimeException.class, () ->
                stockService.reserve(1L, 1L, 100));
    }

    @Test
    void releaseReservation_shouldDecreaseReserved() {
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L))
                .thenReturn(Optional.of(testStock));
        when(stockRepository.save(any(Stock.class))).thenReturn(testStock);

        stockService.releaseReservation(1L, 1L, 5, false);

        assertEquals(5, testStock.getReserved()); // было 10 - 5
        assertEquals(100, testStock.getQuantity()); // не изменилось
    }

    @Test
    void releaseReservation_shouldDecreaseQuantityWhenShipped() {
        when(stockRepository.findByProductIdAndFacilityId(1L, 1L))
                .thenReturn(Optional.of(testStock));
        when(stockRepository.save(any(Stock.class))).thenReturn(testStock);

        stockService.releaseReservation(1L, 1L, 10, true);

        assertEquals(0, testStock.getReserved());
        assertEquals(90, testStock.getQuantity()); // 100 - 10
    }

    @Test
    void getTotalStock_shouldReturnSum() {
        when(stockRepository.getTotalQuantityByProductId(1L)).thenReturn(500);

        Integer total = stockService.getTotalStock(1L);

        assertEquals(500, total);
    }
}
