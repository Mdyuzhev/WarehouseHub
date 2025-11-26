package com.warehouse.controller;

import com.warehouse.model.Product;
import com.warehouse.model.Role;
import com.warehouse.model.User;
import com.warehouse.repository.ProductRepository;
import com.warehouse.repository.UserRepository;
import com.warehouse.security.JwtService;
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
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
        RestAssured.port = port;
        productRepository.deleteAll();
        userRepository.deleteAll();

        // Create test user with EMPLOYEE role (can create/delete products)
        User employeeUser = new User();
        employeeUser.setUsername("testemployee");
        employeeUser.setPassword(passwordEncoder.encode("password"));
        employeeUser.setFullName("Test Employee");
        employeeUser.setRole(Role.EMPLOYEE);
        employeeUser.setEnabled(true);
        employeeUser = userRepository.save(employeeUser);
        employeeToken = jwtService.generateToken(employeeUser);
    }

    @Test
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
    void shouldReturnBadRequestWhenNameIsEmpty() {
        Product product = new Product();
        product.setName("");
        product.setQuantity(10);
        product.setPrice(99.99);

        // Log the response to debug
        Response response = given()
                .contentType(ContentType.JSON)
                .header("Authorization", "Bearer " + employeeToken)
                .body(product)
        .when()
                .post("/api/products");
        
        System.out.println("Response status: " + response.getStatusCode());
        System.out.println("Response body: " + response.getBody().asString());
        
        assertEquals(400, response.getStatusCode(), "Expected 400 but got " + response.getStatusCode() + ": " + response.getBody().asString());
    }

    @Test
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
