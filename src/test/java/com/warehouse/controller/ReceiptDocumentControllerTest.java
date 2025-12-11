package com.warehouse.controller;

import com.warehouse.model.*;
import com.warehouse.repository.*;
import com.warehouse.security.JwtService;
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;
import java.util.Map;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

/**
 * Integration тесты для ReceiptDocumentController
 * WH-272: Receipt Documents - Блок 5
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class ReceiptDocumentControllerTest {

    @LocalServerPort
    private int port;

    @Autowired
    private ReceiptDocumentRepository receiptRepository;

    @Autowired
    private FacilityRepository facilityRepository;

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private StockRepository stockRepository;

    @Autowired
    private JwtService jwtService;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private String employeeToken;
    private String managerToken;
    private User employeeUser;
    private User managerUser;
    private Facility testFacility;
    private Product testProduct;

    @BeforeEach
    void setUp() {
        RestAssured.reset();
        RestAssured.port = port;

        // Clean up
        receiptRepository.deleteAll();
        stockRepository.deleteAll();

        // Create test users
        employeeUser = userRepository.findByUsername("test_employee").orElse(null);
        if (employeeUser == null) {
            employeeUser = new User();
            employeeUser.setUsername("test_employee");
            employeeUser.setPassword(passwordEncoder.encode("password123"));
            employeeUser.setFullName("Test Employee");
            employeeUser.setEmail("employee@test.com");
            employeeUser.setRole(Role.EMPLOYEE);
            employeeUser.setEnabled(true);
            employeeUser = userRepository.saveAndFlush(employeeUser);
        }
        employeeToken = jwtService.generateToken(employeeUser);

        managerUser = userRepository.findByUsername("test_manager").orElse(null);
        if (managerUser == null) {
            managerUser = new User();
            managerUser.setUsername("test_manager");
            managerUser.setPassword(passwordEncoder.encode("password123"));
            managerUser.setFullName("Test Manager");
            managerUser.setEmail("manager@test.com");
            managerUser.setRole(Role.MANAGER);
            managerUser.setEnabled(true);
            managerUser = userRepository.saveAndFlush(managerUser);
        }
        managerToken = jwtService.generateToken(managerUser);

        // Create test facility
        testFacility = facilityRepository.findByCode("WH-TEST-001").orElse(null);
        if (testFacility == null) {
            testFacility = Facility.builder()
                    .code("WH-TEST-001")
                    .name("Test Warehouse")
                    .type(FacilityType.WH)
                    .status("ACTIVE")
                    .address("Test Address")
                    .build();
            testFacility = facilityRepository.saveAndFlush(testFacility);
        }

        // Create test product
        testProduct = productRepository.findAll().stream().findFirst().orElse(null);
        if (testProduct == null) {
            testProduct = new Product();
            testProduct.setName("Test Product");
            testProduct.setQuantity(1000);
            testProduct.setPrice(99.99);
            testProduct = productRepository.saveAndFlush(testProduct);
        }
    }

    @Test
    @DisplayName("Should create receipt successfully with valid data (EMPLOYEE)")
    void testCreateReceipt_Authorized() {
        Map<String, Object> request = Map.of(
                "facilityId", testFacility.getId(),
                "supplierName", "Test Supplier",
                "notes", "Test notes",
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 100
                        )
                )
        );

        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(request)
        .when()
                .post("/api/receipts")
        .then()
                .statusCode(201)
                .body("id", notNullValue())
                .body("documentNumber", startsWith("RCP-WH-TEST-001-"))
                .body("status", equalTo("DRAFT"))
                .body("facilityCode", equalTo("WH-TEST-001"))
                .body("supplierName", equalTo("Test Supplier"))
                .body("totalExpected", equalTo(100))
                .body("totalActual", equalTo(0))
                .body("items.size()", equalTo(1));
    }

    @Test
    @DisplayName("Should return 401/403 when creating receipt without authentication")
    void testCreateReceipt_Unauthorized() {
        Map<String, Object> request = Map.of(
                "facilityId", testFacility.getId(),
                "supplierName", "Test Supplier",
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 100
                        )
                )
        );

        given()
                .contentType(ContentType.JSON)
                .body(request)
        .when()
                .post("/api/receipts")
        .then()
                .statusCode(anyOf(is(401), is(403)));
    }

    @Test
    @DisplayName("Should get receipts by facility")
    void testGetByFacility_ReturnsList() {
        // Create a receipt first
        Map<String, Object> request = Map.of(
                "facilityId", testFacility.getId(),
                "supplierName", "Test Supplier",
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 50
                        )
                )
        );

        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(request)
                .post("/api/receipts");

        // Get receipts by facility
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/receipts/facility/" + testFacility.getId())
        .then()
                .statusCode(200)
                .body("size()", greaterThanOrEqualTo(1))
                .body("[0].facilityId", equalTo(testFacility.getId().intValue()));
    }

    @Test
    @DisplayName("Should approve receipt (MANAGER role required)")
    void testApprove_ManagerOnly() {
        // Create receipt
        Map<String, Object> createRequest = Map.of(
                "facilityId", testFacility.getId(),
                "supplierName", "Test Supplier",
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 100
                        )
                )
        );

        Integer receiptId = given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(createRequest)
                .post("/api/receipts")
                .then()
                .extract()
                .path("id");

        // Approve with MANAGER token
        given()
                .header("Authorization", "Bearer " + managerToken)
        .when()
                .post("/api/receipts/" + receiptId + "/approve")
        .then()
                .statusCode(200)
                .body("status", equalTo("APPROVED"))
                .body("approvedByUsername", equalTo("test_manager"));
    }

    @Test
    @DisplayName("Should confirm receipt and update stock")
    void testConfirm_UpdatesStock() {
        // Create and approve receipt
        Map<String, Object> createRequest = Map.of(
                "facilityId", testFacility.getId(),
                "supplierName", "Test Supplier",
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 100
                        )
                )
        );

        Integer receiptId = given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(createRequest)
                .post("/api/receipts")
                .then()
                .extract()
                .path("id");

        Integer itemId = given()
                .header("Authorization", "Bearer " + employeeToken)
                .get("/api/receipts/" + receiptId)
                .then()
                .extract()
                .path("items[0].id");

        // Approve
        given()
                .header("Authorization", "Bearer " + managerToken)
                .post("/api/receipts/" + receiptId + "/approve");

        // Confirm with actual quantities
        Map<String, Object> confirmRequest = Map.of(
                "items", List.of(
                        Map.of(
                                "itemId", itemId,
                                "actualQuantity", 95
                        )
                )
        );

        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(confirmRequest)
        .when()
                .post("/api/receipts/" + receiptId + "/confirm")
        .then()
                .statusCode(200)
                .body("status", equalTo("CONFIRMED"))
                .body("totalActual", equalTo(95));

        // Verify stock was updated
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/stock/product/" + testProduct.getId() + "/facility/" + testFacility.getId())
        .then()
                .statusCode(200)
                .body("quantity", greaterThanOrEqualTo(95));
    }

    @Test
    @DisplayName("Should delete DRAFT receipt (MANAGER role)")
    void testDelete_OnlyDraft() {
        // Create receipt
        Map<String, Object> createRequest = Map.of(
                "facilityId", testFacility.getId(),
                "supplierName", "Test Supplier",
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 100
                        )
                )
        );

        Integer receiptId = given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(createRequest)
                .post("/api/receipts")
                .then()
                .extract()
                .path("id");

        // Delete with MANAGER token
        given()
                .header("Authorization", "Bearer " + managerToken)
        .when()
                .delete("/api/receipts/" + receiptId)
        .then()
                .statusCode(204);

        // Verify deleted
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/receipts/" + receiptId)
        .then()
                .statusCode(404);
    }

    @Test
    @DisplayName("Should not delete APPROVED receipt")
    void testDelete_NotDraft_Returns400() {
        // Create and approve receipt
        Map<String, Object> createRequest = Map.of(
                "facilityId", testFacility.getId(),
                "supplierName", "Test Supplier",
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 100
                        )
                )
        );

        Integer receiptId = given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(createRequest)
                .post("/api/receipts")
                .then()
                .extract()
                .path("id");

        // Approve
        given()
                .header("Authorization", "Bearer " + managerToken)
                .post("/api/receipts/" + receiptId + "/approve");

        // Try to delete - should fail
        given()
                .header("Authorization", "Bearer " + managerToken)
        .when()
                .delete("/api/receipts/" + receiptId)
        .then()
                .statusCode(400);
    }
}
