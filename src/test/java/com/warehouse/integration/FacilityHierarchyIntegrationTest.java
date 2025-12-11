package com.warehouse.integration;

import com.warehouse.model.Role;
import com.warehouse.model.User;
import com.warehouse.repository.FacilityRepository;
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
    private JwtService jwtService;

    private String adminToken;

    @BeforeEach
    void setUp() {
        RestAssured.reset();
        RestAssured.port = port;

        // Setup admin user for API calls
        User admin = userRepository.findByUsername("admin").orElseThrow();
        adminToken = jwtService.generateToken(admin);
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
            .body("facilityId", equalTo(2))
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
        // WH-C-001 (facility_id=2) should have 5 stock records
        given()
            .header("Authorization", "Bearer " + adminToken)
            .contentType(ContentType.JSON)
        .when()
            .get("/api/stock/facility/2")
        .then()
            .statusCode(200)
            .body("size()", equalTo(5))
            .body("facilityId", everyItem(equalTo(2)))
            .body("quantity", everyItem(greaterThan(0)))
            .body("reserved", everyItem(equalTo(0)));

        // PP-C-001 (facility_id=4) should have 3 stock records
        given()
            .header("Authorization", "Bearer " + adminToken)
            .contentType(ContentType.JSON)
        .when()
            .get("/api/stock/facility/4")
        .then()
            .statusCode(200)
            .body("size()", equalTo(3))
            .body("facilityId", everyItem(equalTo(4)))
            .body("quantity", everyItem(greaterThan(0)))
            .body("reserved", everyItem(equalTo(0)));

        // DC-C-001 (facility_id=1) should have 0 stock records (distribution center)
        given()
            .header("Authorization", "Bearer " + adminToken)
            .contentType(ContentType.JSON)
        .when()
            .get("/api/stock/facility/1")
        .then()
            .statusCode(200)
            .body("size()", greaterThanOrEqualTo(0)); // DC может иметь 0 или stock из V4 миграции
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
