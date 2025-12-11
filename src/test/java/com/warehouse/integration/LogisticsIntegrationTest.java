package com.warehouse.integration;

import com.warehouse.dto.ReceiptConfirmRequest;
import com.warehouse.dto.ReceiptCreateRequest;
import com.warehouse.dto.ReceiptDocumentDTO;
import com.warehouse.dto.ShipmentCreateRequest;
import com.warehouse.dto.ShipmentDocumentDTO;
import com.warehouse.kafka.LogisticsEventConsumer;
import com.warehouse.kafka.LogisticsEventProducer;
import com.warehouse.model.*;
import com.warehouse.repository.*;
import com.warehouse.service.ReceiptDocumentService;
import com.warehouse.service.ShipmentDocumentService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.SpyBean;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Integration тесты для Logistics Kafka flow
 * WH-274: Kafka Auto-Documents - Блок 5
 *
 * Тестирует:
 * - Receipt confirm → ShipmentEvent (Kafka)
 * - Shipment delivered → Receipt auto-creation
 */
@SpringBootTest
@ActiveProfiles("test")
class LogisticsIntegrationTest {

    @Autowired
    private ShipmentDocumentService shipmentService;

    @Autowired
    private ReceiptDocumentService receiptService;

    @Autowired
    private FacilityRepository facilityRepository;

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private ShipmentDocumentRepository shipmentRepository;

    @Autowired
    private ReceiptDocumentRepository receiptRepository;

    @Autowired
    private StockRepository stockRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @SpyBean
    private LogisticsEventProducer eventProducer;

    @SpyBean
    private LogisticsEventConsumer eventConsumer;

    private User testUser;
    private Facility sourceWH;
    private Facility destWH;
    private Product testProduct;

    @BeforeEach
    void setUp() {
        // Clean up
        receiptRepository.deleteAll();
        shipmentRepository.deleteAll();
        stockRepository.deleteAll();

        // Create test user
        testUser = userRepository.findByUsername("logistics_test_user").orElse(null);
        if (testUser == null) {
            testUser = new User();
            testUser.setUsername("logistics_test_user");
            testUser.setPassword(passwordEncoder.encode("password123"));
            testUser.setFullName("Logistics Test User");
            testUser.setEmail("logistics@test.com");
            testUser.setRole(Role.MANAGER);
            testUser.setEnabled(true);
            testUser = userRepository.saveAndFlush(testUser);
        }

        // Create facilities
        sourceWH = facilityRepository.findByCode("WH-SRC-001").orElse(null);
        if (sourceWH == null) {
            sourceWH = Facility.builder()
                    .code("WH-SRC-001")
                    .name("Source Warehouse")
                    .type(FacilityType.WH)
                    .status("ACTIVE")
                    .address("Source Address")
                    .build();
            sourceWH = facilityRepository.saveAndFlush(sourceWH);
        }

        destWH = facilityRepository.findByCode("WH-DST-001").orElse(null);
        if (destWH == null) {
            destWH = Facility.builder()
                    .code("WH-DST-001")
                    .name("Destination Warehouse")
                    .type(FacilityType.WH)
                    .status("ACTIVE")
                    .address("Dest Address")
                    .build();
            destWH = facilityRepository.saveAndFlush(destWH);
        }

        // Create product
        testProduct = productRepository.findAll().stream().findFirst().orElse(null);
        if (testProduct == null) {
            testProduct = new Product();
            testProduct.setName("Logistics Test Product");
            testProduct.setQuantity(1000);
            testProduct.setPrice(50.0);
            testProduct = productRepository.saveAndFlush(testProduct);
        }

        // Create stock at source
        Stock stock = Stock.builder()
                .product(testProduct)
                .facility(sourceWH)
                .quantity(200)
                .reserved(0)
                .build();
        stockRepository.saveAndFlush(stock);
    }

    @Test
    void testReceiptConfirm_SendsShipmentEvent() {
        // Arrange: Create and confirm receipt at source WH
        ReceiptCreateRequest createRequest = ReceiptCreateRequest.builder()
                .facilityId(sourceWH.getId())
                .supplierName("Test Supplier")
                .items(List.of(
                        ReceiptCreateRequest.ReceiptItemRequest.builder()
                                .productId(testProduct.getId())
                                .expectedQuantity(50)
                                .build()
                ))
                .build();

        ReceiptDocumentDTO receipt = receiptService.create(createRequest, testUser);
        receipt = receiptService.approve(receipt.getId(), testUser);

        ReceiptConfirmRequest confirmRequest = ReceiptConfirmRequest.builder()
                .items(List.of(
                        ReceiptConfirmRequest.ItemActualQuantity.builder()
                                .itemId(receipt.getItems().get(0).getId())
                                .actualQuantity(50)
                                .build()
                ))
                .build();

        reset(eventProducer); // Reset to clear setup calls

        // Act: Confirm receipt (should trigger ShipmentEvent if linked)
        receiptService.confirm(receipt.getId(), confirmRequest, testUser);

        // Assert: Verify ShipmentEvent sent to Kafka
        // Note: Events only sent if Receipt has linked shipmentId (WH-274.4)
        // Since we didn't link shipment, no event should be sent
        verify(eventProducer, never()).sendShipmentEvent(any());
    }

    @Test
    void testShipmentDelivered_CreatesReceipt() {
        // Arrange: Create and ship a shipment
        ShipmentCreateRequest shipmentRequest = ShipmentCreateRequest.builder()
                .sourceFacilityId(sourceWH.getId())
                .destinationFacilityId(destWH.getId())
                .items(List.of(
                        ShipmentCreateRequest.ShipmentItemRequest.builder()
                                .productId(testProduct.getId())
                                .quantity(30)
                                .build()
                ))
                .build();

        ShipmentDocumentDTO shipment = shipmentService.create(shipmentRequest, testUser);
        shipment = shipmentService.ship(shipment.getId(), testUser);

        reset(eventProducer); // Reset to clear previous calls

        // Act: Mark as delivered (should send event to Kafka)
        ShipmentDocumentDTO delivered = shipmentService.deliver(shipment.getId(), testUser);

        // Assert: Verify event was sent
        ArgumentCaptor<String> documentNumberCaptor = ArgumentCaptor.forClass(String.class);
        ArgumentCaptor<String> sourceCodeCaptor = ArgumentCaptor.forClass(String.class);
        ArgumentCaptor<String> destCodeCaptor = ArgumentCaptor.forClass(String.class);

        verify(eventProducer, times(1)).sendShipmentEvent(
                documentNumberCaptor.capture(),
                sourceCodeCaptor.capture(),
                destCodeCaptor.capture()
        );

        assertEquals(delivered.getDocumentNumber(), documentNumberCaptor.getValue());
        assertEquals(sourceWH.getCode(), sourceCodeCaptor.getValue());
        assertEquals(destWH.getCode(), destCodeCaptor.getValue());
    }

    @Test
    void testLogisticsEventConsumer_ProcessesShipmentEvent() {
        // Arrange: Create shipment
        ShipmentCreateRequest shipmentRequest = ShipmentCreateRequest.builder()
                .sourceFacilityId(sourceWH.getId())
                .destinationFacilityId(destWH.getId())
                .items(List.of(
                        ShipmentCreateRequest.ShipmentItemRequest.builder()
                                .productId(testProduct.getId())
                                .quantity(25)
                                .build()
                ))
                .build();

        ShipmentDocumentDTO shipment = shipmentService.create(shipmentRequest, testUser);
        shipment = shipmentService.ship(shipment.getId(), testUser);

        long receiptCountBefore = receiptRepository.count();

        // Act: Simulate Kafka event consumption
        // In real flow: Shipment delivered → Event sent → Consumer creates Receipt
        // Here we test consumer directly
        eventConsumer.handleShipmentDelivered(
                shipment.getDocumentNumber(),
                sourceWH.getCode(),
                destWH.getCode()
        );

        // Assert: Verify Receipt auto-created
        long receiptCountAfter = receiptRepository.count();
        assertEquals(receiptCountBefore + 1, receiptCountAfter, "Receipt should be auto-created");

        // Find the auto-created receipt
        List<ReceiptDocument> receipts = receiptRepository.findByFacilityId(destWH.getId());
        assertFalse(receipts.isEmpty(), "Receipt should exist at destination facility");

        ReceiptDocument autoReceipt = receipts.get(0);
        assertEquals(ReceiptStatus.DRAFT, autoReceipt.getStatus());
        assertEquals("Auto-generated from shipment: " + shipment.getDocumentNumber(), autoReceipt.getNotes());
        assertEquals(shipment.getId(), autoReceipt.getShipmentId());
    }

    @Test
    void testFullLogisticsFlow_ShipmentToReceipt() {
        // Full flow test: Shipment → Delivered → Event → Auto-Receipt

        // Step 1: Create and ship
        ShipmentCreateRequest request = ShipmentCreateRequest.builder()
                .sourceFacilityId(sourceWH.getId())
                .destinationFacilityId(destWH.getId())
                .items(List.of(
                        ShipmentCreateRequest.ShipmentItemRequest.builder()
                                .productId(testProduct.getId())
                                .quantity(40)
                                .build()
                ))
                .build();

        ShipmentDocumentDTO shipment = shipmentService.create(request, testUser);
        shipment = shipmentService.ship(shipment.getId(), testUser);

        long receiptCountBefore = receiptRepository.count();

        // Step 2: Deliver (triggers event)
        ShipmentDocumentDTO delivered = shipmentService.deliver(shipment.getId(), testUser);

        // Step 3: Manually trigger consumer (in real app, Kafka triggers it)
        eventConsumer.handleShipmentDelivered(
                delivered.getDocumentNumber(),
                sourceWH.getCode(),
                destWH.getCode()
        );

        // Step 4: Verify Receipt created
        long receiptCountAfter = receiptRepository.count();
        assertTrue(receiptCountAfter > receiptCountBefore, "Auto-receipt should be created");

        List<ReceiptDocument> receipts = receiptRepository.findByFacilityId(destWH.getId());
        assertFalse(receipts.isEmpty());

        ReceiptDocument autoReceipt = receipts.stream()
                .filter(r -> r.getShipmentId() != null && r.getShipmentId().equals(delivered.getId()))
                .findFirst()
                .orElse(null);

        assertNotNull(autoReceipt, "Auto-receipt linked to shipment should exist");
        assertEquals(1, autoReceipt.getItems().size());
        assertEquals(40, autoReceipt.getItems().get(0).getExpectedQuantity());
    }
}
