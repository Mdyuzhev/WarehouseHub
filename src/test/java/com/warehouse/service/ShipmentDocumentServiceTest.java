package com.warehouse.service;

import com.warehouse.dto.ShipmentCreateRequest;
import com.warehouse.dto.ShipmentDocumentDTO;
import com.warehouse.model.*;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.ProductRepository;
import com.warehouse.repository.ShipmentDocumentRepository;
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
 * Unit тесты для ShipmentDocumentService
 * WH-273: Shipment Documents - Блок 5
 */
@ExtendWith(MockitoExtension.class)
class ShipmentDocumentServiceTest {

    @Mock
    private ShipmentDocumentRepository shipmentRepository;

    @Mock
    private FacilityRepository facilityRepository;

    @Mock
    private ProductRepository productRepository;

    @Mock
    private StockService stockService;

    @InjectMocks
    private ShipmentDocumentService shipmentService;

    private User testUser;
    private Facility sourceFacility;
    private Facility destFacility;
    private Product testProduct;
    private ShipmentDocument testShipment;

    @BeforeEach
    void setUp() {
        testUser = new User();
        testUser.setId(1L);
        testUser.setUsername("testuser");
        testUser.setRole(Role.EMPLOYEE);

        sourceFacility = Facility.builder()
                .id(2L)
                .code("WH-C-001")
                .name("Source Warehouse")
                .type(FacilityType.WH)
                .status("ACTIVE")
                .build();

        destFacility = Facility.builder()
                .id(3L)
                .code("WH-C-002")
                .name("Dest Warehouse")
                .type(FacilityType.WH)
                .status("ACTIVE")
                .build();

        testProduct = new Product();
        testProduct.setId(1L);
        testProduct.setName("Test Product");
        testProduct.setQuantity(1000);
        testProduct.setPrice(99.99);

        testShipment = ShipmentDocument.builder()
                .id(1L)
                .documentNumber("SHP-WH-C-001-20251211-001")
                .sourceFacility(sourceFacility)
                .destinationFacility(destFacility)
                .status(ShipmentStatus.DRAFT)
                .createdBy(testUser)
                .createdAt(LocalDateTime.now())
                .items(new ArrayList<>())
                .build();

        ShipmentItem item = ShipmentItem.builder()
                .id(1L)
                .shipmentDocument(testShipment)
                .product(testProduct)
                .quantity(100)
                .build();
        testShipment.getItems().add(item);
    }

    @Test
    void testCreateShipment_Valid() {
        ShipmentCreateRequest request = ShipmentCreateRequest.builder()
                .sourceFacilityId(2L)
                .destinationFacilityId(3L)
                .items(List.of(
                        ShipmentCreateRequest.ShipmentItemRequest.builder()
                                .productId(1L)
                                .quantity(100)
                                .build()
                ))
                .build();

        when(facilityRepository.findById(2L)).thenReturn(Optional.of(sourceFacility));
        when(facilityRepository.findById(3L)).thenReturn(Optional.of(destFacility));
        when(productRepository.findById(1L)).thenReturn(Optional.of(testProduct));
        when(shipmentRepository.countByFacilityAndDate(any(), any(), any())).thenReturn(0L);
        when(shipmentRepository.save(any(ShipmentDocument.class))).thenAnswer(inv -> {
            ShipmentDocument saved = inv.getArgument(0);
            saved.setId(1L);
            return saved;
        });

        ShipmentDocumentDTO result = shipmentService.create(request, testUser);

        assertNotNull(result);
        assertEquals(ShipmentStatus.DRAFT, result.getStatus());
        assertEquals(1, result.getItems().size());
        assertEquals(100, result.getTotalQuantity());
        assertTrue(result.getDocumentNumber().startsWith("SHP-WH-C-001-"));
        verify(shipmentRepository, times(1)).save(any(ShipmentDocument.class));
    }

    @Test
    void testCreateShipment_EmptyItems() {
        ShipmentCreateRequest request = ShipmentCreateRequest.builder()
                .sourceFacilityId(2L)
                .destinationFacilityId(3L)
                .items(Collections.emptyList())
                .build();

        when(facilityRepository.findById(2L)).thenReturn(Optional.of(sourceFacility));
        when(facilityRepository.findById(3L)).thenReturn(Optional.of(destFacility));

        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            shipmentService.create(request, testUser);
        });

        assertEquals("Shipment must have at least one item", exception.getMessage());
        verify(shipmentRepository, never()).save(any());
    }

    @Test
    void testApprove_ReservesStock() {
        when(shipmentRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testShipment));
        when(shipmentRepository.save(any(ShipmentDocument.class))).thenAnswer(inv -> inv.getArgument(0));
        when(stockService.reserve(any(), any(), any())).thenReturn(null);

        ShipmentDocumentDTO result = shipmentService.approve(1L, testUser);

        assertNotNull(result);
        assertEquals(ShipmentStatus.APPROVED, result.getStatus());
        assertEquals("testuser", result.getApprovedByUsername());
        verify(stockService, times(1)).reserve(1L, 2L, 100);
    }

    @Test
    void testApprove_NotDraft() {
        testShipment.setStatus(ShipmentStatus.SHIPPED);
        when(shipmentRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testShipment));

        IllegalStateException exception = assertThrows(IllegalStateException.class, () -> {
            shipmentService.approve(1L, testUser);
        });

        assertTrue(exception.getMessage().contains("Only DRAFT shipments can be approved"));
        verify(stockService, never()).reserve(any(), any(), any());
    }

    @Test
    void testShip_DeductsStock() {
        testShipment.setStatus(ShipmentStatus.APPROVED);
        when(shipmentRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testShipment));
        when(shipmentRepository.save(any(ShipmentDocument.class))).thenAnswer(inv -> inv.getArgument(0));
        when(stockService.releaseReservation(any(), any(), any(), anyBoolean())).thenReturn(null);

        ShipmentDocumentDTO result = shipmentService.ship(1L, testUser);

        assertNotNull(result);
        assertEquals(ShipmentStatus.SHIPPED, result.getStatus());
        assertEquals("testuser", result.getShippedByUsername());
        verify(stockService, times(1)).releaseReservation(1L, 2L, 100, true);
    }

    @Test
    void testShip_NotApproved() {
        testShipment.setStatus(ShipmentStatus.DRAFT);
        when(shipmentRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testShipment));

        IllegalStateException exception = assertThrows(IllegalStateException.class, () -> {
            shipmentService.ship(1L, testUser);
        });

        assertTrue(exception.getMessage().contains("Only APPROVED shipments can be shipped"));
        verify(stockService, never()).releaseReservation(any(), any(), any(), anyBoolean());
    }

    @Test
    void testDeliver_OnlyShipped() {
        testShipment.setStatus(ShipmentStatus.SHIPPED);
        when(shipmentRepository.findById(1L)).thenReturn(Optional.of(testShipment));
        when(shipmentRepository.save(any(ShipmentDocument.class))).thenAnswer(inv -> inv.getArgument(0));

        ShipmentDocumentDTO result = shipmentService.deliver(1L);

        assertNotNull(result);
        assertEquals(ShipmentStatus.DELIVERED, result.getStatus());
        assertNotNull(result.getDeliveredAt());
    }

    @Test
    void testCancel_ReleasesReservation() {
        testShipment.setStatus(ShipmentStatus.APPROVED);
        when(shipmentRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testShipment));
        when(stockService.releaseReservation(any(), any(), any(), anyBoolean())).thenReturn(null);

        shipmentService.cancel(1L);

        verify(stockService, times(1)).releaseReservation(1L, 2L, 100, false);
        verify(shipmentRepository, times(1)).delete(testShipment);
    }

    @Test
    void testCancel_DraftNoReservation() {
        when(shipmentRepository.findByIdWithItems(1L)).thenReturn(Optional.of(testShipment));

        shipmentService.cancel(1L);

        verify(stockService, never()).releaseReservation(any(), any(), any(), anyBoolean());
        verify(shipmentRepository, times(1)).delete(testShipment);
    }
}
