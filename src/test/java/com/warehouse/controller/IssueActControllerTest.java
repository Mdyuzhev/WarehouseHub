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
 * Integration тесты для IssueActController
 * WH-275: Issue Acts - Блок 5
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class IssueActControllerTest {

    @LocalServerPort
    private int port;

    @Autowired
    private IssueActRepository issueActRepository;

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
    private Facility ppFacility;
    private Product testProduct;

    @BeforeEach
    void setUp() {
        RestAssured.reset();
        RestAssured.port = port;

        // Clean up
        issueActRepository.deleteAll();

        // Create test user
        employeeUser = userRepository.findByUsername("test_issue_employee").orElse(null);
        if (employeeUser == null) {
            employeeUser = new User();
            employeeUser.setUsername("test_issue_employee");
            employeeUser.setPassword(passwordEncoder.encode("password123"));
            employeeUser.setFullName("Test Employee");
            employeeUser.setEmail("issue@test.com");
            employeeUser.setRole(Role.EMPLOYEE);
            employeeUser.setEnabled(true);
            employeeUser = userRepository.saveAndFlush(employeeUser);
        }
        employeeToken = jwtService.generateToken(employeeUser);

        // Create test PP facility
        ppFacility = facilityRepository.findByCode("PP-TEST-001").orElse(null);
        if (ppFacility == null) {
            ppFacility = Facility.builder()
                    .code("PP-TEST-001")
                    .name("Test Pickup Point")
                    .type(FacilityType.PP)
                    .status("ACTIVE")
                    .address("Test Address")
                    .build();
            ppFacility = facilityRepository.saveAndFlush(ppFacility);
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

        // Create stock for PP
        Stock stock = stockRepository.findByProductIdAndFacilityId(testProduct.getId(), ppFacility.getId())
                .orElse(null);
        if (stock == null) {
            stock = Stock.builder()
                    .product(testProduct)
                    .facility(ppFacility)
                    .quantity(100)
                    .reserved(0)
                    .build();
            stockRepository.saveAndFlush(stock);
        }
    }

    @Test
    void testCreateIssueAct_Authorized() {
        Map<String, Object> request = Map.of(
                "facilityId", ppFacility.getId(),
                "customerName", "John Doe",
                "customerPhone", "+7900123456",
                "items", List.of(
                        Map.of("productId", testProduct.getId(), "quantity", 10)
                )
        );

        given()
                .header("Authorization", "Bearer " + employeeToken)
                .contentType(ContentType.JSON)
                .body(request)
        .when()
                .post("/api/issue-acts")
        .then()
                .statusCode(201)
                .body("status", equalTo("DRAFT"))
                .body("customerName", equalTo("John Doe"))
                .body("facilityCode", equalTo("PP-TEST-001"))
                .body("items.size()", equalTo(1))
                .body("totalQuantity", equalTo(10))
                .body("documentNumber", startsWith("ISS-PP-TEST-001-"));
    }

    @Test
    void testCreateIssueAct_Unauthorized() {
        Map<String, Object> request = Map.of(
                "facilityId", ppFacility.getId(),
                "customerName", "John Doe",
                "items", List.of(
                        Map.of("productId", testProduct.getId(), "quantity", 10)
                )
        );

        given()
                .contentType(ContentType.JSON)
                .body(request)
        .when()
                .post("/api/issue-acts")
        .then()
                .statusCode(401);
    }

    @Test
    void testGetIssueActById() {
        // Create issue act first
        Map<String, Object> createRequest = Map.of(
                "facilityId", ppFacility.getId(),
                "customerName", "John Doe",
                "items", List.of(
                        Map.of("productId", testProduct.getId(), "quantity", 10)
                )
        );

        Long issueActId = given()
                .header("Authorization", "Bearer " + employeeToken)
                .contentType(ContentType.JSON)
                .body(createRequest)
        .when()
                .post("/api/issue-acts")
        .then()
                .statusCode(201)
                .extract().path("id");

        // Get by ID
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/issue-acts/" + issueActId)
        .then()
                .statusCode(200)
                .body("id", equalTo(issueActId.intValue()))
                .body("status", equalTo("DRAFT"));
    }

    @Test
    void testCompleteIssueAct() {
        // Create issue act
        Map<String, Object> createRequest = Map.of(
                "facilityId", ppFacility.getId(),
                "customerName", "John Doe",
                "items", List.of(
                        Map.of("productId", testProduct.getId(), "quantity", 5)
                )
        );

        Long issueActId = given()
                .header("Authorization", "Bearer " + employeeToken)
                .contentType(ContentType.JSON)
                .body(createRequest)
        .when()
                .post("/api/issue-acts")
        .then()
                .statusCode(201)
                .extract().path("id");

        // Complete
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .post("/api/issue-acts/" + issueActId + "/complete")
        .then()
                .statusCode(200)
                .body("status", equalTo("COMPLETED"))
                .body("completedAt", notNullValue());
    }

    @Test
    void testGetByFacility() {
        // Create 2 issue acts
        Map<String, Object> request1 = Map.of(
                "facilityId", ppFacility.getId(),
                "customerName", "Customer 1",
                "items", List.of(Map.of("productId", testProduct.getId(), "quantity", 5))
        );

        Map<String, Object> request2 = Map.of(
                "facilityId", ppFacility.getId(),
                "customerName", "Customer 2",
                "items", List.of(Map.of("productId", testProduct.getId(), "quantity", 3))
        );

        given()
                .header("Authorization", "Bearer " + employeeToken)
                .contentType(ContentType.JSON)
                .body(request1)
        .when()
                .post("/api/issue-acts")
        .then()
                .statusCode(201);

        given()
                .header("Authorization", "Bearer " + employeeToken)
                .contentType(ContentType.JSON)
                .body(request2)
        .when()
                .post("/api/issue-acts")
        .then()
                .statusCode(201);

        // Get by facility
        given()
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/issue-acts/facility/" + ppFacility.getId())
        .then()
                .statusCode(200)
                .body("size()", greaterThanOrEqualTo(2));
    }
}
