package com.warehouse.service;

import com.warehouse.dto.ReceiptConfirmRequest;
import com.warehouse.dto.ReceiptCreateRequest;
import com.warehouse.dto.ReceiptDocumentDTO;
import com.warehouse.model.*;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.ProductRepository;
import com.warehouse.repository.ReceiptDocumentRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit тесты для ReceiptDocumentService
 * WH-272: Receipt Documents - Блок 5
 */
@ExtendWith(MockitoExtension.class)
class ReceiptDocumentServiceTest {

    @Mock
    private ReceiptDocumentRepository receiptRepository;

    @Mock
    private FacilityRepository facilityRepository;

    @Mock
    private ProductRepository productRepository;

    @Mock
    private StockService stockService;

    @InjectMocks
    private ReceiptDocumentService receiptService;

    private User testUser;
    private Facility testFacility;
    private Product testProduct;
    private ReceiptDocument testReceipt;

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
        testProduct.setQuantity(100);
        testProduct.setPrice(99.99);

        testReceipt = ReceiptDocument.builder()
                .id(1L)
                .documentNumber("RCP-WH-C-001-20251211-001")
                .facility(testFacility)
                .supplierName("Test Supplier")
                .status(ReceiptStatus.DRAFT)
                .createdBy(testUser)
                .createdAt(LocalDateTime.now())
                .items(new ArrayList<>())
                .build();

        ReceiptItem item = ReceiptItem.builder()
                .id(1L)
                .receiptDocument(testReceipt)
                .product(testProduct)
                .expectedQuantity(100)
                .actualQuantity(0)
                .build();
        testReceipt.getItems().add(item);
    }

    @Test
    void testCreateReceipt_Valid() {
        // Arrange
        ReceiptCreateRequest request = ReceiptCreateRequest.builder()
                .facilityId(2L)
                .supplierName("Test Supplier")
                .items(List.of(
                        ReceiptCreateRequest.ReceiptItemRequest.builder()
                                .productId(1L)
                                .expectedQuantity(100)
                                .build()
                ))
                .build();

        when(facilityRepository.findById(2L)).thenReturn(Optional.of(testFacility));
        when(productRepository.findById(1L)).thenReturn(Optional.of(testProduct));
        when(receiptRepository.countByFacilityAndDate(any(), any(), any())).thenReturn(0L);
        when(receiptRepository.save(any(ReceiptDocument.class))).thenAnswer(inv -> {
            ReceiptDocument saved = inv.getArgument(0);
            saved.setId(1L);
            return saved;
        });

        // Act
        ReceiptDocumentDTO result = receiptService.create(request, testUser);

        // Assert
        assertNotNull(result);
        assertEquals(ReceiptStatus.DRAFT, result.getStatus());
        assertEquals("Test Supplier", result.getSupplierName());
        assertEquals(1, result.getItems().size());
        assertEquals(100, result.getTotalExpected());
        assertTrue(result.getDocumentNumber().startsWith("RCP-WH-C-001-"));
        verify(receiptRepository, times(1)).save(any(ReceiptDocument.class));
    }

    @Test
    void testCreateReceipt_EmptyItems() {
        // Arrange
        ReceiptCreateRequest request = ReceiptCreateRequest.builder()
                .facilityId(2L)
                .supplierName("Test Supplier")
                .items(Collections.emptyList())
                .build();

        when(facilityRepository.findById(2L)).thenReturn(Optional.of(testFacility));

        // Act & Assert
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            receiptService.create(request, testUser);
        });

        assertEquals("Receipt must have at least one item", exception.getMessage());
        verify(receiptRepository, never()).save(any());
    }

    @Test
    void testApprove_FromDraft() {
        // Arrange
        when(receiptRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testReceipt));
        when(receiptRepository.save(any(ReceiptDocument.class))).thenAnswer(inv -> inv.getArgument(0));

        // Act
        ReceiptDocumentDTO result = receiptService.approve(1L, testUser);

        // Assert
        assertNotNull(result);
        assertEquals(ReceiptStatus.APPROVED, result.getStatus());
        assertEquals("testuser", result.getApprovedByUsername());
        assertNotNull(result.getApprovedAt());
        verify(receiptRepository, times(1)).save(any(ReceiptDocument.class));
    }

    @Test
    void testApprove_NotDraft() {
        // Arrange
        testReceipt.setStatus(ReceiptStatus.CONFIRMED);
        when(receiptRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testReceipt));

        // Act & Assert
        IllegalStateException exception = assertThrows(IllegalStateException.class, () -> {
            receiptService.approve(1L, testUser);
        });

        assertTrue(exception.getMessage().contains("Only DRAFT receipts can be approved"));
        verify(receiptRepository, never()).save(any());
    }

    @Test
    void testConfirm_UpdatesStock() {
        // Arrange
        testReceipt.setStatus(ReceiptStatus.APPROVED);
        when(receiptRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testReceipt));
        when(receiptRepository.save(any(ReceiptDocument.class))).thenAnswer(inv -> inv.getArgument(0));
        when(stockService.getStock(1L, 2L)).thenReturn(null); // Stock doesn't exist yet
        when(stockService.setStock(1L, 2L, 95)).thenReturn(null);

        ReceiptConfirmRequest confirmRequest = ReceiptConfirmRequest.builder()
                .items(List.of(
                        ReceiptConfirmRequest.ItemActualQuantity.builder()
                                .itemId(1L)
                                .actualQuantity(95)
                                .build()
                ))
                .build();

        // Act
        ReceiptDocumentDTO result = receiptService.confirm(1L, confirmRequest, testUser);

        // Assert
        assertNotNull(result);
        assertEquals(ReceiptStatus.CONFIRMED, result.getStatus());
        assertEquals(95, result.getTotalActual());
        assertEquals("testuser", result.getConfirmedByUsername());
        verify(stockService, times(1)).setStock(1L, 2L, 95);
    }

    @Test
    void testConfirm_NotApproved() {
        // Arrange
        testReceipt.setStatus(ReceiptStatus.DRAFT);
        when(receiptRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testReceipt));

        ReceiptConfirmRequest confirmRequest = ReceiptConfirmRequest.builder()
                .items(List.of(
                        ReceiptConfirmRequest.ItemActualQuantity.builder()
                                .itemId(1L)
                                .actualQuantity(95)
                                .build()
                ))
                .build();

        // Act & Assert
        IllegalStateException exception = assertThrows(IllegalStateException.class, () -> {
            receiptService.confirm(1L, confirmRequest, testUser);
        });

        assertTrue(exception.getMessage().contains("Only APPROVED receipts can be confirmed"));
        verify(stockService, never()).setStock(any(), any(), any());
    }

    @Test
    void testDelete_OnlyDraft() {
        // Arrange
        when(receiptRepository.findById(1L)).thenReturn(Optional.of(testReceipt));

        // Act
        receiptService.delete(1L);

        // Assert
        verify(receiptRepository, times(1)).delete(testReceipt);
    }

    @Test
    void testDelete_NotDraft_ThrowsException() {
        // Arrange
        testReceipt.setStatus(ReceiptStatus.APPROVED);
        when(receiptRepository.findById(1L)).thenReturn(Optional.of(testReceipt));

        // Act & Assert
        IllegalStateException exception = assertThrows(IllegalStateException.class, () -> {
            receiptService.delete(1L);
        });

        assertTrue(exception.getMessage().contains("Only DRAFT receipts can be deleted"));
        verify(receiptRepository, never()).delete(any());
    }

    @Test
    void testGenerateDocumentNumber() {
        // Arrange
        ReceiptCreateRequest request = ReceiptCreateRequest.builder()
                .facilityId(2L)
                .supplierName("Test Supplier")
                .items(List.of(
                        ReceiptCreateRequest.ReceiptItemRequest.builder()
                                .productId(1L)
                                .expectedQuantity(100)
                                .build()
                ))
                .build();

        when(facilityRepository.findById(2L)).thenReturn(Optional.of(testFacility));
        when(productRepository.findById(1L)).thenReturn(Optional.of(testProduct));
        when(receiptRepository.countByFacilityAndDate(any(), any(), any())).thenReturn(5L); // 5 receipts already exist today
        when(receiptRepository.save(any(ReceiptDocument.class))).thenAnswer(inv -> {
            ReceiptDocument saved = inv.getArgument(0);
            saved.setId(1L);
            return saved;
        });

        // Act
        ReceiptDocumentDTO result = receiptService.create(request, testUser);

        // Assert
        String today = LocalDate.now().format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
        String expectedPattern = "RCP-WH-C-001-" + today + "-006"; // 6th receipt today
        assertEquals(expectedPattern, result.getDocumentNumber());
    }

    @Test
    void testComplete_OnlyConfirmed() {
        // Arrange
        testReceipt.setStatus(ReceiptStatus.CONFIRMED);
        when(receiptRepository.findById(1L)).thenReturn(Optional.of(testReceipt));
        when(receiptRepository.save(any(ReceiptDocument.class))).thenAnswer(inv -> inv.getArgument(0));

        // Act
        ReceiptDocumentDTO result = receiptService.complete(1L);

        // Assert
        assertNotNull(result);
        assertEquals(ReceiptStatus.COMPLETED, result.getStatus());
        verify(receiptRepository, times(1)).save(any(ReceiptDocument.class));
    }

    @Test
    void testComplete_NotConfirmed_ThrowsException() {
        // Arrange
        testReceipt.setStatus(ReceiptStatus.DRAFT);
        when(receiptRepository.findById(1L)).thenReturn(Optional.of(testReceipt));

        // Act & Assert
        IllegalStateException exception = assertThrows(IllegalStateException.class, () -> {
            receiptService.complete(1L);
        });

        assertTrue(exception.getMessage().contains("Only CONFIRMED receipts can be completed"));
        verify(receiptRepository, never()).save(any());
    }
}
