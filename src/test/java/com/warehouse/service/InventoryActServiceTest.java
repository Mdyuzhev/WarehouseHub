package com.warehouse.service;

import com.warehouse.dto.InventoryActCreateRequest;
import com.warehouse.dto.InventoryActDTO;
import com.warehouse.model.*;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.InventoryActRepository;
import com.warehouse.repository.ProductRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit тесты для InventoryActService
 * WH-275: Inventory Acts - Блок 5
 */
@ExtendWith(MockitoExtension.class)
class InventoryActServiceTest {

    @Mock
    private InventoryActRepository inventoryActRepository;

    @Mock
    private FacilityRepository facilityRepository;

    @Mock
    private ProductRepository productRepository;

    @Mock
    private StockService stockService;

    @InjectMocks
    private InventoryActService inventoryActService;

    private User testUser;
    private Facility testFacility;
    private Product testProduct;
    private InventoryAct testInventoryAct;

    @BeforeEach
    void setUp() {
        testUser = new User();
        testUser.setId(1L);
        testUser.setUsername("testuser");
        testUser.setRole(Role.EMPLOYEE);

        testFacility = Facility.builder()
                .id(2L)
                .code("WH-C-001")
                .name("Test Warehouse")
                .type(FacilityType.WH)
                .status("ACTIVE")
                .build();

        testProduct = new Product();
        testProduct.setId(1L);
        testProduct.setName("Test Product");
        testProduct.setQuantity(1000);
        testProduct.setPrice(99.99);

        testInventoryAct = InventoryAct.builder()
                .id(1L)
                .documentNumber("INV-WH-C-001-20251211-001")
                .facility(testFacility)
                .status(InventoryStatus.DRAFT)
                .createdBy(testUser)
                .createdAt(LocalDateTime.now())
                .items(new ArrayList<>())
                .build();

        InventoryActItem item = InventoryActItem.builder()
                .id(1L)
                .inventoryAct(testInventoryAct)
                .product(testProduct)
                .expectedQuantity(100)
                .actualQuantity(95)
                .build();
        testInventoryAct.getItems().add(item);
    }

    @Test
    void testCreate_Valid() {
        // Arrange
        InventoryActCreateRequest request = InventoryActCreateRequest.builder()
                .facilityId(2L)
                .notes("Monthly inventory")
                .items(List.of(
                        InventoryActCreateRequest.InventoryActItemRequest.builder()
                                .productId(1L)
                                .expectedQuantity(100)
                                .actualQuantity(95)
                                .build()
                ))
                .build();

        when(facilityRepository.findById(2L)).thenReturn(Optional.of(testFacility));
        when(productRepository.findById(1L)).thenReturn(Optional.of(testProduct));
        when(inventoryActRepository.countByFacilityAndDate(any(), any(), any())).thenReturn(0L);
        when(inventoryActRepository.save(any(InventoryAct.class))).thenAnswer(inv -> {
            InventoryAct saved = inv.getArgument(0);
            saved.setId(1L);
            return saved;
        });

        // Act
        InventoryActDTO result = inventoryActService.create(request, testUser);

        // Assert
        assertNotNull(result);
        assertEquals(InventoryStatus.DRAFT, result.getStatus());
        assertEquals(1, result.getItems().size());
        assertEquals(100, result.getTotalExpected());
        assertEquals(95, result.getTotalActual());
        assertEquals(-5, result.getTotalDifference());
        assertTrue(result.getDocumentNumber().startsWith("INV-WH-C-001-"));
        verify(inventoryActRepository, times(1)).save(any(InventoryAct.class));
    }

    @Test
    void testCreate_EmptyItems() {
        // Arrange
        InventoryActCreateRequest request = InventoryActCreateRequest.builder()
                .facilityId(2L)
                .items(Collections.emptyList())
                .build();

        when(facilityRepository.findById(2L)).thenReturn(Optional.of(testFacility));

        // Act & Assert
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            inventoryActService.create(request, testUser);
        });

        assertEquals("Inventory act must have at least one item", exception.getMessage());
        verify(inventoryActRepository, never()).save(any());
    }

    @Test
    void testComplete_PositiveDifference() {
        // Arrange: actual > expected (найдено больше товара)
        testInventoryAct.getItems().get(0).setExpectedQuantity(100);
        testInventoryAct.getItems().get(0).setActualQuantity(110);

        when(inventoryActRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testInventoryAct));
        when(inventoryActRepository.save(any(InventoryAct.class))).thenAnswer(inv -> inv.getArgument(0));

        // Act
        InventoryActDTO result = inventoryActService.complete(1L, testUser);

        // Assert
        assertNotNull(result);
        assertEquals(InventoryStatus.COMPLETED, result.getStatus());
        assertNotNull(result.getCompletedAt());
        verify(stockService, times(1)).adjustStock(1L, 2L, +10); // Positive = increase
        verify(inventoryActRepository, times(1)).save(any(InventoryAct.class));
    }

    @Test
    void testComplete_NegativeDifference() {
        // Arrange: actual < expected (недостача)
        testInventoryAct.getItems().get(0).setExpectedQuantity(100);
        testInventoryAct.getItems().get(0).setActualQuantity(85);

        when(inventoryActRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testInventoryAct));
        when(inventoryActRepository.save(any(InventoryAct.class))).thenAnswer(inv -> inv.getArgument(0));

        // Act
        InventoryActDTO result = inventoryActService.complete(1L, testUser);

        // Assert
        assertNotNull(result);
        assertEquals(InventoryStatus.COMPLETED, result.getStatus());
        verify(stockService, times(1)).adjustStock(1L, 2L, -15); // Negative = decrease
    }

    @Test
    void testComplete_ZeroDifference() {
        // Arrange: actual = expected (все совпало)
        testInventoryAct.getItems().get(0).setExpectedQuantity(100);
        testInventoryAct.getItems().get(0).setActualQuantity(100);

        when(inventoryActRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testInventoryAct));
        when(inventoryActRepository.save(any(InventoryAct.class))).thenAnswer(inv -> inv.getArgument(0));

        // Act
        InventoryActDTO result = inventoryActService.complete(1L, testUser);

        // Assert
        assertNotNull(result);
        assertEquals(InventoryStatus.COMPLETED, result.getStatus());
        verify(stockService, never()).adjustStock(any(), any(), any()); // No adjustment needed
    }

    @Test
    void testComplete_NotDraft_ThrowsException() {
        // Arrange
        testInventoryAct.setStatus(InventoryStatus.COMPLETED);
        when(inventoryActRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testInventoryAct));

        // Act & Assert
        IllegalStateException exception = assertThrows(IllegalStateException.class, () -> {
            inventoryActService.complete(1L, testUser);
        });

        assertTrue(exception.getMessage().contains("Only DRAFT inventory acts can be completed"));
        verify(stockService, never()).adjustStock(any(), any(), any());
        verify(inventoryActRepository, never()).save(any());
    }

    @Test
    void testDelete_OnlyDraft() {
        // Arrange
        when(inventoryActRepository.findById(1L)).thenReturn(Optional.of(testInventoryAct));

        // Act
        inventoryActService.delete(1L);

        // Assert
        verify(inventoryActRepository, times(1)).delete(testInventoryAct);
    }

    @Test
    void testDelete_NotDraft_ThrowsException() {
        // Arrange
        testInventoryAct.setStatus(InventoryStatus.COMPLETED);
        when(inventoryActRepository.findById(1L)).thenReturn(Optional.of(testInventoryAct));

        // Act & Assert
        IllegalStateException exception = assertThrows(IllegalStateException.class, () -> {
            inventoryActService.delete(1L);
        });

        assertTrue(exception.getMessage().contains("Only DRAFT inventory acts can be deleted"));
        verify(inventoryActRepository, never()).delete(any());
    }

    @Test
    void testGetById() {
        // Arrange
        when(inventoryActRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testInventoryAct));

        // Act
        InventoryActDTO result = inventoryActService.getById(1L);

        // Assert
        assertNotNull(result);
        assertEquals(1L, result.getId());
        assertEquals("INV-WH-C-001-20251211-001", result.getDocumentNumber());
        assertEquals(1, result.getItems().size());
    }

    @Test
    void testGetByFacility() {
        // Arrange
        when(inventoryActRepository.findByFacilityId(2L)).thenReturn(List.of(testInventoryAct));

        // Act
        List<InventoryActDTO> results = inventoryActService.getByFacility(2L);

        // Assert
        assertNotNull(results);
        assertEquals(1, results.size());
        assertEquals(testInventoryAct.getId(), results.get(0).getId());
    }
}
