package com.warehouse.integration;

import com.warehouse.model.*;
import com.warehouse.repository.FacilityRepository;
import com.warehouse.repository.ProductRepository;
import com.warehouse.repository.StockRepository;
import com.warehouse.repository.UserRepository;
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
 * Integration тесты для facility hierarchy
 * WH-271.4: Facility Hierarchy Integration Tests
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@Epic("Data Model")
@Feature("Facility Hierarchy")
@DisplayName("Facility Hierarchy Integration Tests")
class FacilityHierarchyIntegrationTest {

    @LocalServerPort
    private int port;

    @Autowired
    private FacilityRepository facilityRepository;

    @Autowired
    private StockRepository stockRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private JwtService jwtService;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private String adminToken;
    private Facility dc;
    private Facility whNorth;
    private Facility whSouth;
    private Facility pp1;
    private Facility pp2;
    private Facility pp3;
    private Facility pp4;

    @BeforeEach
    void setUp() {
        RestAssured.reset();
        RestAssured.port = port;

        // Clear all test data
        stockRepository.deleteAll();
        facilityRepository.deleteAll();
        productRepository.deleteAll();
        userRepository.deleteAll();

        // Create admin user (SUPER_USER)
        User admin = new User();
        admin.setUsername("admin");
        admin.setPassword(passwordEncoder.encode("admin123"));
        admin.setEmail("admin@warehouse.local");
        admin.setFullName("System Administrator");
        admin.setRole(Role.SUPER_USER);
        admin.setEnabled(true);
        admin = userRepository.saveAndFlush(admin);
        adminToken = jwtService.generateToken(admin);

        // Create 5 products (matching V1 migration)
        Product laptop = productRepository.save(new Product(null, "Laptop", 10, 999.99, "High performance laptop", "Electronics"));
        Product mouse = productRepository.save(new Product(null, "Mouse", 50, 29.99, "Wireless mouse", "Electronics"));
        Product keyboard = productRepository.save(new Product(null, "Keyboard", 30, 79.99, "Mechanical keyboard", "Electronics"));
        Product monitor = productRepository.save(new Product(null, "Monitor", 15, 399.99, "27 inch 4K monitor", "Electronics"));
        Product headphones = productRepository.save(new Product(null, "Headphones", 25, 149.99, "Noise-cancelling headphones", "Electronics"));

        // Create 7 facilities (matching V5 migration)
        dc = facilityRepository.save(Facility.builder()
            .code("DC-C-001")
            .name("Distribution Center Central")
            .type(FacilityType.DC)
            .parentId(null)
            .address("Central District")
            .status("ACTIVE")
            .build());

        whNorth = facilityRepository.save(Facility.builder()
            .code("WH-C-001")
            .name("Warehouse North")
            .type(FacilityType.WH)
            .parentId(dc.getId())
            .address("North Region")
            .status("ACTIVE")
            .build());

        whSouth = facilityRepository.save(Facility.builder()
            .code("WH-C-002")
            .name("Warehouse South")
            .type(FacilityType.WH)
            .parentId(dc.getId())
            .address("South Region")
            .status("ACTIVE")
            .build());

        pp1 = facilityRepository.save(Facility.builder()
            .code("PP-C-001")
            .name("Pickup Point 1")
            .type(FacilityType.PP)
            .parentId(whNorth.getId())
            .address("North-1 Location")
            .status("ACTIVE")
            .build());

        pp2 = facilityRepository.save(Facility.builder()
            .code("PP-C-002")
            .name("Pickup Point 2")
            .type(FacilityType.PP)
            .parentId(whNorth.getId())
            .address("North-2 Location")
            .status("ACTIVE")
            .build());

        pp3 = facilityRepository.save(Facility.builder()
            .code("PP-C-003")
            .name("Pickup Point 3")
            .type(FacilityType.PP)
            .parentId(whSouth.getId())
            .address("South-1 Location")
            .status("ACTIVE")
            .build());

        pp4 = facilityRepository.save(Facility.builder()
            .code("PP-C-004")
            .name("Pickup Point 4")
            .type(FacilityType.PP)
            .parentId(whSouth.getId())
            .address("South-2 Location")
            .status("ACTIVE")
            .build());

        // Create 7 facility users (matching V6 migration)
        User dcManager = new User();
        dcManager.setUsername("dc_manager");
        dcManager.setPassword(passwordEncoder.encode("password123"));
        dcManager.setEmail("dc_manager@warehouse.local");
        dcManager.setFullName("Менеджер РЦ");
        dcManager.setRole(Role.MANAGER);
        dcManager.setEnabled(true);
        dcManager.setFacilityType(FacilityType.DC);
        dcManager.setFacilityId(dc.getId());
        userRepository.save(dcManager);

        User whNorthOp = new User();
        whNorthOp.setUsername("wh_north_op");
        whNorthOp.setPassword(passwordEncoder.encode("password123"));
        whNorthOp.setEmail("wh_north_op@warehouse.local");
        whNorthOp.setFullName("Оператор Север");
        whNorthOp.setRole(Role.EMPLOYEE);
        whNorthOp.setEnabled(true);
        whNorthOp.setFacilityType(FacilityType.WH);
        whNorthOp.setFacilityId(whNorth.getId());
        userRepository.save(whNorthOp);

        User whSouthOp = new User();
        whSouthOp.setUsername("wh_south_op");
        whSouthOp.setPassword(passwordEncoder.encode("password123"));
        whSouthOp.setEmail("wh_south_op@warehouse.local");
        whSouthOp.setFullName("Оператор Юг");
        whSouthOp.setRole(Role.EMPLOYEE);
        whSouthOp.setEnabled(true);
        whSouthOp.setFacilityType(FacilityType.WH);
        whSouthOp.setFacilityId(whSouth.getId());
        userRepository.save(whSouthOp);

        User pp1Op = new User();
        pp1Op.setUsername("pp_1_op");
        pp1Op.setPassword(passwordEncoder.encode("password123"));
        pp1Op.setEmail("pp_1_op@warehouse.local");
        pp1Op.setFullName("Оператор ПВЗ 1");
        pp1Op.setRole(Role.EMPLOYEE);
        pp1Op.setEnabled(true);
        pp1Op.setFacilityType(FacilityType.PP);
        pp1Op.setFacilityId(pp1.getId());
        userRepository.save(pp1Op);

        User pp2Op = new User();
        pp2Op.setUsername("pp_2_op");
        pp2Op.setPassword(passwordEncoder.encode("password123"));
        pp2Op.setEmail("pp_2_op@warehouse.local");
        pp2Op.setFullName("Оператор ПВЗ 2");
        pp2Op.setRole(Role.EMPLOYEE);
        pp2Op.setEnabled(true);
        pp2Op.setFacilityType(FacilityType.PP);
        pp2Op.setFacilityId(pp2.getId());
        userRepository.save(pp2Op);

        User pp3Op = new User();
        pp3Op.setUsername("pp_3_op");
        pp3Op.setPassword(passwordEncoder.encode("password123"));
        pp3Op.setEmail("pp_3_op@warehouse.local");
        pp3Op.setFullName("Оператор ПВЗ 3");
        pp3Op.setRole(Role.EMPLOYEE);
        pp3Op.setEnabled(true);
        pp3Op.setFacilityType(FacilityType.PP);
        pp3Op.setFacilityId(pp3.getId());
        userRepository.save(pp3Op);

        User pp4Op = new User();
        pp4Op.setUsername("pp_4_op");
        pp4Op.setPassword(passwordEncoder.encode("password123"));
        pp4Op.setEmail("pp_4_op@warehouse.local");
        pp4Op.setFullName("Оператор ПВЗ 4");
        pp4Op.setRole(Role.EMPLOYEE);
        pp4Op.setEnabled(true);
        pp4Op.setFacilityType(FacilityType.PP);
        pp4Op.setFacilityId(pp4.getId());
        userRepository.save(pp4Op);

        // Create stock records (matching V7 migration)
        // WH-C-001 (whNorth): 5 products
        stockRepository.save(Stock.builder().product(laptop).facility(whNorth).quantity(150).reserved(0).build());
        stockRepository.save(Stock.builder().product(mouse).facility(whNorth).quantity(200).reserved(0).build());
        stockRepository.save(Stock.builder().product(keyboard).facility(whNorth).quantity(120).reserved(0).build());
        stockRepository.save(Stock.builder().product(monitor).facility(whNorth).quantity(80).reserved(0).build());
        stockRepository.save(Stock.builder().product(headphones).facility(whNorth).quantity(100).reserved(0).build());

        // WH-C-002 (whSouth): 5 products
        stockRepository.save(Stock.builder().product(laptop).facility(whSouth).quantity(180).reserved(0).build());
        stockRepository.save(Stock.builder().product(mouse).facility(whSouth).quantity(190).reserved(0).build());
        stockRepository.save(Stock.builder().product(keyboard).facility(whSouth).quantity(140).reserved(0).build());
        stockRepository.save(Stock.builder().product(monitor).facility(whSouth).quantity(90).reserved(0).build());
        stockRepository.save(Stock.builder().product(headphones).facility(whSouth).quantity(110).reserved(0).build());

        // PP-C-001 (pp1): 3 products
        stockRepository.save(Stock.builder().product(laptop).facility(pp1).quantity(25).reserved(0).build());
        stockRepository.save(Stock.builder().product(mouse).facility(pp1).quantity(50).reserved(0).build());
        stockRepository.save(Stock.builder().product(keyboard).facility(pp1).quantity(35).reserved(0).build());

        // PP-C-002 (pp2): 3 products
        stockRepository.save(Stock.builder().product(laptop).facility(pp2).quantity(30).reserved(0).build());
        stockRepository.save(Stock.builder().product(mouse).facility(pp2).quantity(45).reserved(0).build());
        stockRepository.save(Stock.builder().product(keyboard).facility(pp2).quantity(40).reserved(0).build());

        // PP-C-003 (pp3): 3 products
        stockRepository.save(Stock.builder().product(laptop).facility(pp3).quantity(20).reserved(0).build());
        stockRepository.save(Stock.builder().product(mouse).facility(pp3).quantity(48).reserved(0).build());
        stockRepository.save(Stock.builder().product(keyboard).facility(pp3).quantity(32).reserved(0).build());

        // PP-C-004 (pp4): 3 products
        stockRepository.save(Stock.builder().product(laptop).facility(pp4).quantity(28).reserved(0).build());
        stockRepository.save(Stock.builder().product(mouse).facility(pp4).quantity(42).reserved(0).build());
        stockRepository.save(Stock.builder().product(keyboard).facility(pp4).quantity(38).reserved(0).build());

        // DC-C-001 (dc): no stock - distribution center
    }

    @Test
    @Story("Facility Tree")
    @Severity(SeverityLevel.CRITICAL)
    @Description("Проверяет структуру дерева facilities: 7 объектов, 3 уровня (DC → WH → PP)")
    void testFacilityTreeStructure() {
        given()
            .header("Authorization", "Bearer " + adminToken)
            .contentType(ContentType.JSON)
        .when()
            .get("/api/facilities/tree")
        .then()
            .statusCode(200)
            .body("size()", equalTo(1)) // 1 root (DC)
            .body("[0].code", equalTo("DC-C-001"))
            .body("[0].type", equalTo("DC"))
            .body("[0].children.size()", equalTo(2)) // DC has 2 WH children
            .body("[0].children[0].type", equalTo("WH"))
            .body("[0].children[1].type", equalTo("WH"))
            .body("[0].children[0].children.size()", equalTo(2)) // First WH has 2 PP children
            .body("[0].children[1].children.size()", equalTo(2)); // Second WH has 2 PP children
    }

    @Test
    @Story("User Facility Binding")
    @Severity(SeverityLevel.CRITICAL)
    @Description("Проверяет что JWT токен operator'а содержит facility claims")
    void testUserFacilityBinding() {
        String token = given()
            .contentType(ContentType.JSON)
            .body("{\"username\":\"wh_north_op\",\"password\":\"password123\"}")
        .when()
            .post("/api/auth/login")
        .then()
            .statusCode(200)
            .body("username", equalTo("wh_north_op"))
            .body("role", equalTo("EMPLOYEE"))
            .body("facilityType", equalTo("WH"))
            .body("facilityId", equalTo(whNorth.getId().intValue()))
            .body("facilityCode", equalTo("WH-C-001"))
            .body("token", notNullValue())
        .extract()
            .path("token");

        // Verify token can be used for API calls
        given()
            .header("Authorization", "Bearer " + token)
            .contentType(ContentType.JSON)
        .when()
            .get("/api/facilities/tree")
        .then()
            .statusCode(200);
    }

    @Test
    @Story("Stock by Facility")
    @Severity(SeverityLevel.CRITICAL)
    @Description("Проверяет количество stock records: WH имеют 5 записей, PP имеют 3 записи")
    void testStockByFacility() {
        // WH-C-001 (whNorth) should have 5 stock records
        given()
            .header("Authorization", "Bearer " + adminToken)
            .contentType(ContentType.JSON)
        .when()
            .get("/api/stock/facility/" + whNorth.getId())
        .then()
            .statusCode(200)
            .body("size()", equalTo(5))
            .body("facilityId", everyItem(equalTo(whNorth.getId().intValue())))
            .body("quantity", everyItem(greaterThan(0)))
            .body("reserved", everyItem(equalTo(0)));

        // PP-C-001 (pp1) should have 3 stock records
        given()
            .header("Authorization", "Bearer " + adminToken)
            .contentType(ContentType.JSON)
        .when()
            .get("/api/stock/facility/" + pp1.getId())
        .then()
            .statusCode(200)
            .body("size()", equalTo(3))
            .body("facilityId", everyItem(equalTo(pp1.getId().intValue())))
            .body("quantity", everyItem(greaterThan(0)))
            .body("reserved", everyItem(equalTo(0)));

        // DC-C-001 (dc) should have 0 stock records (distribution center)
        given()
            .header("Authorization", "Bearer " + adminToken)
            .contentType(ContentType.JSON)
        .when()
            .get("/api/stock/facility/" + dc.getId())
        .then()
            .statusCode(200)
            .body("size()", equalTo(0)); // DC should have no stock
    }

    @Test
    @Story("Hierarchy Navigation")
    @Severity(SeverityLevel.NORMAL)
    @Description("Проверяет parent-child связи: DC→2 WH, каждый WH→2 PP")
    void testHierarchyNavigation() {
        // Get all facilities
        var facilities = given()
            .header("Authorization", "Bearer " + adminToken)
            .contentType(ContentType.JSON)
        .when()
            .get("/api/facilities")
        .then()
            .statusCode(200)
            .body("size()", greaterThanOrEqualTo(7))
        .extract()
            .jsonPath()
            .getList("$");

        // Count facilities by type
        long dcCount = facilities.stream()
            .filter(f -> ((java.util.Map<?, ?>) f).get("type").equals("DC"))
            .count();
        long whCount = facilities.stream()
            .filter(f -> ((java.util.Map<?, ?>) f).get("type").equals("WH"))
            .count();
        long ppCount = facilities.stream()
            .filter(f -> ((java.util.Map<?, ?>) f).get("type").equals("PP"))
            .count();

        Assertions.assertTrue(dcCount >= 1, "Should have at least 1 DC");
        Assertions.assertTrue(whCount >= 2, "Should have at least 2 WH facilities");
        Assertions.assertTrue(ppCount >= 4, "Should have at least 4 PP facilities");

        // Verify WH facilities have parent_id pointing to DC
        var whFacilities = facilities.stream()
            .filter(f -> ((java.util.Map<?, ?>) f).get("type").equals("WH"))
            .toList();

        for (Object wh : whFacilities) {
            var whMap = (java.util.Map<?, ?>) wh;
            if (whMap.get("code").toString().startsWith("WH-C-")) {
                Assertions.assertNotNull(whMap.get("parentId"),
                    "WH facility should have parentId");
            }
        }

        // Verify PP facilities have parent_id pointing to WH
        var ppFacilities = facilities.stream()
            .filter(f -> ((java.util.Map<?, ?>) f).get("type").equals("PP"))
            .toList();

        for (Object pp : ppFacilities) {
            var ppMap = (java.util.Map<?, ?>) pp;
            if (ppMap.get("code").toString().startsWith("PP-C-")) {
                Assertions.assertNotNull(ppMap.get("parentId"),
                    "PP facility should have parentId");
            }
        }
    }
}
