package com.warehouse.service;

import com.warehouse.dto.IssueActCreateRequest;
import com.warehouse.dto.IssueActDTO;
import com.warehouse.model.*;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.IssueActRepository;
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
 * Unit тесты для IssueActService
 * WH-275: Issue Acts - Блок 5
 */
@ExtendWith(MockitoExtension.class)
class IssueActServiceTest {

    @Mock
    private IssueActRepository issueActRepository;

    @Mock
    private FacilityRepository facilityRepository;

    @Mock
    private ProductRepository productRepository;

    @Mock
    private StockService stockService;

    @InjectMocks
    private IssueActService issueActService;

    private User testUser;
    private Facility ppFacility;
    private Facility whFacility;
    private Product testProduct;
    private IssueAct testIssueAct;

    @BeforeEach
    void setUp() {
        testUser = new User();
        testUser.setId(1L);
        testUser.setUsername("testuser");
        testUser.setRole(Role.EMPLOYEE);

        ppFacility = Facility.builder()
                .id(4L)
                .code("PP-C-001")
                .name("Test Pickup Point")
                .type(FacilityType.PP)
                .status("ACTIVE")
                .build();

        whFacility = Facility.builder()
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

        testIssueAct = IssueAct.builder()
                .id(1L)
                .documentNumber("ISS-PP-C-001-20251211-001")
                .facility(ppFacility)
                .customerName("John Doe")
                .customerPhone("+7900123456")
                .status(IssueStatus.DRAFT)
                .createdBy(testUser)
                .createdAt(LocalDateTime.now())
                .items(new ArrayList<>())
                .build();

        IssueActItem item = IssueActItem.builder()
                .id(1L)
                .issueAct(testIssueAct)
                .product(testProduct)
                .quantity(10)
                .build();
        testIssueAct.getItems().add(item);
    }

    @Test
    void testCreate_Valid() {
        // Arrange
        IssueActCreateRequest request = IssueActCreateRequest.builder()
                .facilityId(4L)
                .customerName("John Doe")
                .customerPhone("+7900123456")
                .items(List.of(
                        IssueActCreateRequest.IssueActItemRequest.builder()
                                .productId(1L)
                                .quantity(10)
                                .build()
                ))
                .build();

        when(facilityRepository.findById(4L)).thenReturn(Optional.of(ppFacility));
        when(productRepository.findById(1L)).thenReturn(Optional.of(testProduct));
        when(issueActRepository.countByFacilityAndDate(any(), any(), any())).thenReturn(0L);
        when(issueActRepository.save(any(IssueAct.class))).thenAnswer(inv -> {
            IssueAct saved = inv.getArgument(0);
            saved.setId(1L);
            return saved;
        });

        // Act
        IssueActDTO result = issueActService.create(request, testUser);

        // Assert
        assertNotNull(result);
        assertEquals(IssueStatus.DRAFT, result.getStatus());
        assertEquals("John Doe", result.getCustomerName());
        assertEquals(1, result.getItems().size());
        assertEquals(10, result.getTotalQuantity());
        assertTrue(result.getDocumentNumber().startsWith("ISS-PP-C-001-"));
        verify(issueActRepository, times(1)).save(any(IssueAct.class));
    }

    @Test
    void testCreate_NotPP_ThrowsException() {
        // Arrange
        IssueActCreateRequest request = IssueActCreateRequest.builder()
                .facilityId(2L)
                .customerName("John Doe")
                .items(List.of(
                        IssueActCreateRequest.IssueActItemRequest.builder()
                                .productId(1L)
                                .quantity(10)
                                .build()
                ))
                .build();

        when(facilityRepository.findById(2L)).thenReturn(Optional.of(whFacility));

        // Act & Assert
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            issueActService.create(request, testUser);
        });

        assertTrue(exception.getMessage().contains("Issue acts can only be created for pickup points"));
        verify(issueActRepository, never()).save(any());
    }

    @Test
    void testCreate_EmptyItems() {
        // Arrange
        IssueActCreateRequest request = IssueActCreateRequest.builder()
                .facilityId(4L)
                .customerName("John Doe")
                .items(Collections.emptyList())
                .build();

        when(facilityRepository.findById(4L)).thenReturn(Optional.of(ppFacility));

        // Act & Assert
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            issueActService.create(request, testUser);
        });

        assertEquals("Issue act must have at least one item", exception.getMessage());
        verify(issueActRepository, never()).save(any());
    }

    @Test
    void testComplete_DeductsStock() {
        // Arrange
        when(issueActRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testIssueAct));
        when(issueActRepository.save(any(IssueAct.class))).thenAnswer(inv -> inv.getArgument(0));

        // Act
        IssueActDTO result = issueActService.complete(1L, testUser);

        // Assert
        assertNotNull(result);
        assertEquals(IssueStatus.COMPLETED, result.getStatus());
        assertNotNull(result.getCompletedAt());
        verify(stockService, times(1)).adjustStock(1L, 4L, -10); // Negative = deduction
        verify(issueActRepository, times(1)).save(any(IssueAct.class));
    }

    @Test
    void testComplete_NotDraft_ThrowsException() {
        // Arrange
        testIssueAct.setStatus(IssueStatus.COMPLETED);
        when(issueActRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testIssueAct));

        // Act & Assert
        IllegalStateException exception = assertThrows(IllegalStateException.class, () -> {
            issueActService.complete(1L, testUser);
        });

        assertTrue(exception.getMessage().contains("Only DRAFT issue acts can be completed"));
        verify(stockService, never()).adjustStock(any(), any(), any());
        verify(issueActRepository, never()).save(any());
    }

    @Test
    void testDelete_OnlyDraft() {
        // Arrange
        when(issueActRepository.findById(1L)).thenReturn(Optional.of(testIssueAct));

        // Act
        issueActService.delete(1L);

        // Assert
        verify(issueActRepository, times(1)).delete(testIssueAct);
    }

    @Test
    void testDelete_NotDraft_ThrowsException() {
        // Arrange
        testIssueAct.setStatus(IssueStatus.COMPLETED);
        when(issueActRepository.findById(1L)).thenReturn(Optional.of(testIssueAct));

        // Act & Assert
        IllegalStateException exception = assertThrows(IllegalStateException.class, () -> {
            issueActService.delete(1L);
        });

        assertTrue(exception.getMessage().contains("Only DRAFT issue acts can be deleted"));
        verify(issueActRepository, never()).delete(any());
    }

    @Test
    void testGetById() {
        // Arrange
        when(issueActRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testIssueAct));

        // Act
        IssueActDTO result = issueActService.getById(1L);

        // Assert
        assertNotNull(result);
        assertEquals(1L, result.getId());
        assertEquals("ISS-PP-C-001-20251211-001", result.getDocumentNumber());
        assertEquals(1, result.getItems().size());
    }

    @Test
    void testGetByFacility() {
        // Arrange
        when(issueActRepository.findByFacilityId(4L)).thenReturn(List.of(testIssueAct));

        // Act
        List<IssueActDTO> results = issueActService.getByFacility(4L);

        // Assert
        assertNotNull(results);
        assertEquals(1, results.size());
        assertEquals(testIssueAct.getId(), results.get(0).getId());
    }
}
