package com.warehouse.integration;

import com.warehouse.model.*;
import com.warehouse.repository.*;
import com.warehouse.security.JwtService;
import io.qameta.allure.*;
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

/**
 * Integration тесты для StockController
 * WH-297: Stock Controller Integration Tests
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@Epic("API")
@Feature("Stock Management")
@DisplayName("Stock Controller Integration Tests")
@SuppressWarnings("null")
class StockControllerIntegrationTest {

    @LocalServerPort
    private int port;

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private FacilityRepository facilityRepository;

    @Autowired
    private StockRepository stockRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private JwtService jwtService;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private String employeeToken;
    private String managerToken;
    private Product testProduct;
    private Facility testFacility;

    @BeforeEach
    void setUp() {
        RestAssured.reset();
        RestAssured.port = port;

        // Clean up
        stockRepository.deleteAll();

        // Setup test users
        User employeeUser = userRepository.findByUsername("stock_test_employee").orElse(null);
        if (employeeUser == null) {
            employeeUser = new User();
            employeeUser.setUsername("stock_test_employee");
            employeeUser.setPassword(passwordEncoder.encode("password"));
            employeeUser.setFullName("Stock Test Employee");
            employeeUser.setRole(Role.EMPLOYEE);
            employeeUser.setEnabled(true);
            employeeUser = userRepository.saveAndFlush(employeeUser);
        }
        employeeToken = jwtService.generateToken(employeeUser);

        User managerUser = userRepository.findByUsername("stock_test_manager").orElse(null);
        if (managerUser == null) {
            managerUser = new User();
            managerUser.setUsername("stock_test_manager");
            managerUser.setPassword(passwordEncoder.encode("password"));
            managerUser.setFullName("Stock Test Manager");
            managerUser.setRole(Role.MANAGER);
            managerUser.setEnabled(true);
            managerUser = userRepository.saveAndFlush(managerUser);
        }
        managerToken = jwtService.generateToken(managerUser);

        // Setup test product
        Product product = new Product();
        product.setName("Test Stock Product");
        product.setQuantity(0);
        product.setPrice(99.99);
        testProduct = productRepository.save(product);

        // Setup test facility
        testFacility = facilityRepository.findByCode("TEST-WH-STOCK").orElse(null);
        if (testFacility == null) {
            testFacility = java.util.Objects.requireNonNull(facilityRepository.save(Facility.builder()
                    .code("TEST-WH-STOCK")
                    .name("Test Stock Warehouse")
                    .type(FacilityType.WH)
                    .status("ACTIVE")
                    .build()));
        }

        // Setup initial stock
        stockRepository.save(java.util.Objects.requireNonNull(Stock.builder()
                .product(testProduct)
                .facility(testFacility)
                .quantity(100)
                .reserved(0)
                .build()));
    }

    @Test
    @Story("Get Stock")
    @DisplayName("Should return stock list for facility")
    @Severity(SeverityLevel.CRITICAL)
    void getStockByFacility_shouldReturnStockList() {
        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/stock/facility/" + testFacility.getId())
        .then()
                .statusCode(200)
                .body("$", hasSize(greaterThanOrEqualTo(1)))
                .body("[0].quantity", equalTo(100))
                .body("[0].facilityCode", equalTo("TEST-WH-STOCK"));
    }

    @Test
    @Story("Get Stock")
    @DisplayName("Should return stock for specific product and facility")
    @Severity(SeverityLevel.CRITICAL)
    void getStock_shouldReturnStockDTO() {
        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/stock/product/" + testProduct.getId() + "/facility/" + testFacility.getId())
        .then()
                .statusCode(200)
                .body("quantity", equalTo(100))
                .body("reserved", equalTo(0))
                .body("available", equalTo(100));
    }

    @Test
    @Story("Set Stock")
    @DisplayName("Should update stock quantity")
    @Severity(SeverityLevel.CRITICAL)
    void setStock_shouldUpdateQuantity() {
        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body("{\"quantity\": 200}")
        .when()
                .post("/api/stock/product/" + testProduct.getId() + "/facility/" + testFacility.getId())
        .then()
                .statusCode(200)
                .body("quantity", equalTo(200));
    }

    @Test
    @Story("Adjust Stock")
    @DisplayName("Should adjust stock by delta")
    @Severity(SeverityLevel.NORMAL)
    void adjustStock_shouldChangeQuantityByDelta() {
        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body("{\"delta\": 50}")
        .when()
                .patch("/api/stock/product/" + testProduct.getId() + "/facility/" + testFacility.getId() + "/adjust")
        .then()
                .statusCode(200)
                .body("quantity", equalTo(150));
    }

    @Test
    @Story("Reserve Stock")
    @DisplayName("Should reserve stock successfully")
    @Severity(SeverityLevel.CRITICAL)
    void reserve_shouldIncreaseReserved() {
        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + managerToken)
                .body("{\"amount\": 30}")
        .when()
                .post("/api/stock/product/" + testProduct.getId() + "/facility/" + testFacility.getId() + "/reserve")
        .then()
                .statusCode(200)
                .body("reserved", equalTo(30))
                .body("available", equalTo(70));
    }

    @Test
    @Story("Security")
    @DisplayName("Should return 403 without token")
    @Severity(SeverityLevel.CRITICAL)
    void shouldReturnForbiddenWithoutToken() {
        given()
                .contentType(ContentType.JSON)
        .when()
                .get("/api/stock/facility/" + testFacility.getId())
        .then()
                .statusCode(403);
    }

    @Test
    @Story("Get Total Stock")
    @DisplayName("Should return total stock for product")
    @Severity(SeverityLevel.NORMAL)
    void getTotalStock_shouldReturnSum() {
        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
        .when()
                .get("/api/stock/product/" + testProduct.getId() + "/total")
        .then()
                .statusCode(200)
                .body("productId", equalTo(testProduct.getId().intValue()))
                .body("totalQuantity", greaterThanOrEqualTo(100));
    }
}
