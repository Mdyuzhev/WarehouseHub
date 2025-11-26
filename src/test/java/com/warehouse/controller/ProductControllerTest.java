package com.warehouse.controller;

import com.warehouse.model.Product;
import com.warehouse.model.Role;
import com.warehouse.model.User;
import com.warehouse.repository.ProductRepository;
import com.warehouse.repository.UserRepository;
import com.warehouse.security.JwtService;
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class ProductControllerTest {

    @LocalServerPort
    private int port;

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private JwtService jwtService;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private String employeeToken;

    @BeforeEach
    void setUp() {
        RestAssured.reset();
        RestAssured.port = port;
        
        productRepository.deleteAll();
        
        // Do not delete users - reuse existing or create if not exists
        User employeeUser = userRepository.findByUsername("testemployee").orElse(null);
        if (employeeUser == null) {
            employeeUser = new User();
            employeeUser.setUsername("testemployee");
            employeeUser.setPassword(passwordEncoder.encode("password"));
            employeeUser.setFullName("Test Employee");
            employeeUser.setRole(Role.EMPLOYEE);
            employeeUser.setEnabled(true);
            employeeUser = userRepository.saveAndFlush(employeeUser);
        }
        employeeToken = jwtService.generateToken(employeeUser);
    }

    @Test
    @Order(1)
    void shouldCreateProductSuccessfully() {
        Product product = new Product();
        product.setName("Test Product");
        product.setQuantity(10);
        product.setPrice(99.99);

        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(product)
        .when()
                .post("/api/products")
        .then()
                .statusCode(201)
                .body("id", notNullValue())
                .body("name", equalTo("Test Product"))
                .body("quantity", equalTo(10))
                .body("price", equalTo(99.99F));
    }

    @Test
    @Order(2)
    void shouldReturnBadRequestWhenNameIsEmpty() {
        Product product = new Product();
        product.setName("");
        product.setQuantity(10);
        product.setPrice(99.99);

        given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(product)
        .when()
                .post("/api/products")
        .then()
                .statusCode(400);
    }

    @Test
    @Order(3)
    void shouldReturnForbiddenWithoutToken() {
        Product product = new Product();
        product.setName("Test Product");
        product.setQuantity(10);
        product.setPrice(99.99);

        given()
                .contentType(ContentType.JSON)
                .body(product)
        .when()
                .post("/api/products")
        .then()
                .statusCode(403);
    }
}
