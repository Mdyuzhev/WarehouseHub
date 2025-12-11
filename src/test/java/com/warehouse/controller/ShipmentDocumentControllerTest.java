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
 * Integration тесты для ShipmentDocumentController
 * WH-273: Shipment Documents - Блок 5
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class ShipmentDocumentControllerTest {

    @LocalServerPort
    private int port;

    @Autowired
    private ShipmentDocumentRepository shipmentRepository;

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
    private Facility sourceFacility;
    private Facility destFacility;
    private Product testProduct;

    @BeforeEach
    void setUp() {
        RestAssured.reset();
        RestAssured.port = port;

        // Clean up
        shipmentRepository.deleteAll();

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

        // Create source facility
        sourceFacility = facilityRepository.findByCode("WH-SRC-001").orElse(null);
        if (sourceFacility == null) {
            sourceFacility = Facility.builder()
                    .code("WH-SRC-001")
                    .name("Source Warehouse")
                    .type(FacilityType.WH)
                    .status("ACTIVE")
                    .address("Source Address")
                    .build();
            sourceFacility = facilityRepository.saveAndFlush(sourceFacility);
        }

        // Create destination facility
        destFacility = facilityRepository.findByCode("WH-DST-001").orElse(null);
        if (destFacility == null) {
            destFacility = Facility.builder()
                    .code("WH-DST-001")
                    .name("Destination Warehouse")
                    .type(FacilityType.WH)
                    .status("ACTIVE")
                    .address("Destination Address")
                    .build();
            destFacility = facilityRepository.saveAndFlush(destFacility);
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

        // Ensure stock exists for source facility
        Stock stock = stockRepository.findByProductIdAndFacilityId(testProduct.getId(), sourceFacility.getId())
                .orElse(null);
        if (stock == null) {
            stock = Stock.builder()
                    .product(testProduct)
                    .facility(sourceFacility)
                    .quantity(500)
                    .reserved(0)
                    .build();
            stockRepository.saveAndFlush(stock);
        } else {
            stock.setQuantity(500);
            stock.setReserved(0);
            stockRepository.saveAndFlush(stock);
        }
    }

    @Test
    @DisplayName("Should create shipment successfully with valid data (EMPLOYEE)")
    void testCreateShipment_Authorized() {
        Map<String, Object> request = Map.of(
                "sourceFacilityId", sourceFacility.getId(),
                "destinationFacilityId", destFacility.getId(),
                "notes", "Test shipment",
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "quantity", 100
                        )
                )
        );

        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(request)
        .when()
                .post("/api/shipments")
        .then()
                .statusCode(201)
                .body("id", notNullValue())
                .body("documentNumber", startsWith("SHP-WH-SRC-001-"))
                .body("status", equalTo("DRAFT"))
                .body("sourceFacilityCode", equalTo("WH-SRC-001"))
                .body("destinationFacilityCode", equalTo("WH-DST-001"))
                .body("totalQuantity", equalTo(100))
                .body("items.size()", equalTo(1));
    }

    @Test
    @DisplayName("Should return 401/403 when creating shipment without authentication")
    void testCreateShipment_Unauthorized() {
        Map<String, Object> request = Map.of(
                "sourceFacilityId", sourceFacility.getId(),
                "destinationFacilityId", destFacility.getId(),
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "quantity", 100
                        )
                )
        );

        given()
                .contentType(ContentType.JSON)
                .body(request)
        .when()
                .post("/api/shipments")
        .then()
                .statusCode(anyOf(is(401), is(403)));
    }

    @Test
    @DisplayName("Should get shipments by source facility")
    void testGetByFacility_ReturnsList() {
        // Create a shipment first
        Map<String, Object> request = Map.of(
                "sourceFacilityId", sourceFacility.getId(),
                "destinationFacilityId", destFacility.getId(),
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "quantity", 50
                        )
                )
        );

        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(request)
                .post("/api/shipments");

        // Get shipments by facility
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/shipments/facility/" + sourceFacility.getId())
        .then()
                .statusCode(200)
                .body("size()", greaterThanOrEqualTo(1))
                .body("[0].sourceFacilityId", equalTo(sourceFacility.getId().intValue()));
    }

    @Test
    @DisplayName("Should approve shipment and reserve stock (MANAGER role required)")
    void testApprove_ReservesStock() {
        // Create shipment
        Map<String, Object> createRequest = Map.of(
                "sourceFacilityId", sourceFacility.getId(),
                "destinationFacilityId", destFacility.getId(),
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "quantity", 100
                        )
                )
        );

        Integer shipmentId = given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(createRequest)
                .post("/api/shipments")
                .then()
                .extract()
                .path("id");

        // Approve with MANAGER token
        given()
                .header("Authorization", "Bearer " + managerToken)
        .when()
                .post("/api/shipments/" + shipmentId + "/approve")
        .then()
                .statusCode(200)
                .body("status", equalTo("APPROVED"))
                .body("approvedByUsername", equalTo("test_manager"));

        // Verify stock was reserved
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/stock/product/" + testProduct.getId() + "/facility/" + sourceFacility.getId())
        .then()
                .statusCode(200)
                .body("reserved", equalTo(100));
    }

    @Test
    @DisplayName("Should ship shipment and deduct stock")
    void testShip_DeductsStock() {
        // Create and approve shipment
        Map<String, Object> createRequest = Map.of(
                "sourceFacilityId", sourceFacility.getId(),
                "destinationFacilityId", destFacility.getId(),
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "quantity", 100
                        )
                )
        );

        Integer shipmentId = given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(createRequest)
                .post("/api/shipments")
                .then()
                .extract()
                .path("id");

        // Approve
        given()
                .header("Authorization", "Bearer " + managerToken)
                .post("/api/shipments/" + shipmentId + "/approve");

        // Ship
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .post("/api/shipments/" + shipmentId + "/ship")
        .then()
                .statusCode(200)
                .body("status", equalTo("SHIPPED"))
                .body("shippedByUsername", equalTo("test_employee"));

        // Verify stock was deducted
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/stock/product/" + testProduct.getId() + "/facility/" + sourceFacility.getId())
        .then()
                .statusCode(200)
                .body("quantity", equalTo(400)) // 500 - 100
                .body("reserved", equalTo(0)); // reservation released
    }

    @Test
    @DisplayName("Should deliver shipment (SHIPPED → DELIVERED)")
    void testDeliver_OnlyShipped() {
        // Create, approve, and ship
        Map<String, Object> createRequest = Map.of(
                "sourceFacilityId", sourceFacility.getId(),
                "destinationFacilityId", destFacility.getId(),
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "quantity", 50
                        )
                )
        );

        Integer shipmentId = given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(createRequest)
                .post("/api/shipments")
                .then()
                .extract()
                .path("id");

        given()
                .header("Authorization", "Bearer " + managerToken)
                .post("/api/shipments/" + shipmentId + "/approve");

        given()
                .header("Authorization", "Bearer " + employeeToken)
                .post("/api/shipments/" + shipmentId + "/ship");

        // Deliver
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .post("/api/shipments/" + shipmentId + "/deliver")
        .then()
                .statusCode(200)
                .body("status", equalTo("DELIVERED"))
                .body("deliveredAt", notNullValue());
    }

    @Test
    @DisplayName("Should cancel APPROVED shipment and release reservation (MANAGER role)")
    void testCancel_ReleasesReservation() {
        // Create and approve shipment
        Map<String, Object> createRequest = Map.of(
                "sourceFacilityId", sourceFacility.getId(),
                "destinationFacilityId", destFacility.getId(),
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "quantity", 100
                        )
                )
        );

        Integer shipmentId = given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(createRequest)
                .post("/api/shipments")
                .then()
                .extract()
                .path("id");

        // Approve
        given()
                .header("Authorization", "Bearer " + managerToken)
                .post("/api/shipments/" + shipmentId + "/approve");

        // Verify stock is reserved
        given()
                .header("Authorization", "Bearer " + employeeToken)
                .get("/api/stock/product/" + testProduct.getId() + "/facility/" + sourceFacility.getId())
                .then()
                .body("reserved", equalTo(100));

        // Cancel with MANAGER token
        given()
                .header("Authorization", "Bearer " + managerToken)
        .when()
                .post("/api/shipments/" + shipmentId + "/cancel")
        .then()
                .statusCode(204);

        // Verify shipment deleted
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/shipments/" + shipmentId)
        .then()
                .statusCode(404);

        // Verify reservation released
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/stock/product/" + testProduct.getId() + "/facility/" + sourceFacility.getId())
        .then()
                .statusCode(200)
                .body("reserved", equalTo(0));
    }
}
