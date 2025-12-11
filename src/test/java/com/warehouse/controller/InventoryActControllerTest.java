package com.warehouse.controller;

import com.warehouse.model.*;
import com.warehouse.repository.*;
import com.warehouse.security.JwtService;
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeEach;
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
 * Integration тесты для InventoryActController
 * WH-275: Inventory Acts - Блок 5
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class InventoryActControllerTest {

    @LocalServerPort
    private int port;

    @Autowired
    private InventoryActRepository inventoryActRepository;

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
    private User employeeUser;
    private Facility testFacility;
    private Product testProduct;

    @BeforeEach
    void setUp() {
        RestAssured.reset();
        RestAssured.port = port;

        // Clean up
        inventoryActRepository.deleteAll();

        // Create test user
        employeeUser = userRepository.findByUsername("test_inv_employee").orElse(null);
        if (employeeUser == null) {
            employeeUser = new User();
            employeeUser.setUsername("test_inv_employee");
            employeeUser.setPassword(passwordEncoder.encode("password123"));
            employeeUser.setFullName("Test Employee");
            employeeUser.setEmail("inventory@test.com");
            employeeUser.setRole(Role.EMPLOYEE);
            employeeUser.setEnabled(true);
            employeeUser = userRepository.saveAndFlush(employeeUser);
        }
        employeeToken = jwtService.generateToken(employeeUser);

        // Create test facility
        testFacility = facilityRepository.findByCode("WH-INV-001").orElse(null);
        if (testFacility == null) {
            testFacility = Facility.builder()
                    .code("WH-INV-001")
                    .name("Test Warehouse Inventory")
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

        // Create stock
        Stock stock = stockRepository.findByProductIdAndFacilityId(testProduct.getId(), testFacility.getId())
                .orElse(null);
        if (stock == null) {
            stock = Stock.builder()
                    .product(testProduct)
                    .facility(testFacility)
                    .quantity(100)
                    .reserved(0)
                    .build();
            stockRepository.saveAndFlush(stock);
        }
    }

    @Test
    void testCreateInventoryAct_Authorized() {
        Map<String, Object> request = Map.of(
                "facilityId", testFacility.getId(),
                "notes", "Monthly inventory check",
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 100,
                                "actualQuantity", 95
                        )
                )
        );

        given()
                .header("Authorization", "Bearer " + employeeToken)
                .contentType(ContentType.JSON)
                .body(request)
        .when()
                .post("/api/inventory-acts")
        .then()
                .statusCode(201)
                .body("status", equalTo("DRAFT"))
                .body("facilityCode", equalTo("WH-INV-001"))
                .body("items.size()", equalTo(1))
                .body("totalExpected", equalTo(100))
                .body("totalActual", equalTo(95))
                .body("totalDifference", equalTo(-5))
                .body("documentNumber", startsWith("INV-WH-INV-001-"));
    }

    @Test
    void testCreateInventoryAct_Unauthorized() {
        Map<String, Object> request = Map.of(
                "facilityId", testFacility.getId(),
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 100,
                                "actualQuantity", 95
                        )
                )
        );

        given()
                .contentType(ContentType.JSON)
                .body(request)
        .when()
                .post("/api/inventory-acts")
        .then()
                .statusCode(401);
    }

    @Test
    void testGetInventoryActById() {
        // Create inventory act first
        Map<String, Object> createRequest = Map.of(
                "facilityId", testFacility.getId(),
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 100,
                                "actualQuantity", 110
                        )
                )
        );

        Long inventoryActId = given()
                .header("Authorization", "Bearer " + employeeToken)
                .contentType(ContentType.JSON)
                .body(createRequest)
        .when()
                .post("/api/inventory-acts")
        .then()
                .statusCode(201)
                .extract().path("id");

        // Get by ID
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/inventory-acts/" + inventoryActId)
        .then()
                .statusCode(200)
                .body("id", equalTo(inventoryActId.intValue()))
                .body("status", equalTo("DRAFT"))
                .body("totalDifference", equalTo(10));
    }

    @Test
    void testCompleteInventoryAct() {
        // Create inventory act
        Map<String, Object> createRequest = Map.of(
                "facilityId", testFacility.getId(),
                "items", List.of(
                        Map.of(
                                "productId", testProduct.getId(),
                                "expectedQuantity", 100,
                                "actualQuantity", 98
                        )
                )
        );

        Long inventoryActId = given()
                .header("Authorization", "Bearer " + employeeToken)
                .contentType(ContentType.JSON)
                .body(createRequest)
        .when()
                .post("/api/inventory-acts")
        .then()
                .statusCode(201)
                .extract().path("id");

        // Complete
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .post("/api/inventory-acts/" + inventoryActId + "/complete")
        .then()
                .statusCode(200)
                .body("status", equalTo("COMPLETED"))
                .body("completedAt", notNullValue());
    }

    @Test
    void testGetByFacility() {
        // Create 2 inventory acts
        Map<String, Object> request1 = Map.of(
                "facilityId", testFacility.getId(),
                "items", List.of(Map.of("productId", testProduct.getId(), "expectedQuantity", 100, "actualQuantity", 95))
        );

        Map<String, Object> request2 = Map.of(
                "facilityId", testFacility.getId(),
                "items", List.of(Map.of("productId", testProduct.getId(), "expectedQuantity", 50, "actualQuantity", 52))
        );

        given()
                .header("Authorization", "Bearer " + employeeToken)
                .contentType(ContentType.JSON)
                .body(request1)
        .when()
                .post("/api/inventory-acts")
        .then()
                .statusCode(201);

        given()
                .header("Authorization", "Bearer " + employeeToken)
                .contentType(ContentType.JSON)
                .body(request2)
        .when()
                .post("/api/inventory-acts")
        .then()
                .statusCode(201);

        // Get by facility
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/inventory-acts/facility/" + testFacility.getId())
        .then()
                .statusCode(200)
                .body("size()", greaterThanOrEqualTo(2));
    }
}
