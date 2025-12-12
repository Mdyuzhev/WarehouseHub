package com.warehouse.security;

import com.warehouse.model.Role;
import com.warehouse.model.User;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.security.Key;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@ExtendWith(MockitoExtension.class)
@DisplayName("JwtService Tests")
class JwtServiceTest {

    private JwtService jwtService;
    private String secretKey;
    private long jwtExpiration;

    @BeforeEach
    void setUp() {
        // Initialize JwtService without FacilityRepository (null)
        jwtService = new JwtService(null);

        // Set JWT configuration
        secretKey = "bXlTdXBlclNlY3JldEtleUZvckpXVFRva2VuR2VuZXJhdGlvbjEyMzQ1Njc4OTA=";
        jwtExpiration = 3600000L; // 1 hour

        ReflectionTestUtils.setField(jwtService, "secretKey", secretKey);
        ReflectionTestUtils.setField(jwtService, "jwtExpiration", jwtExpiration);
    }

    @Test
    @DisplayName("Should accept token without facility claims (backward compatibility)")
    void shouldAcceptTokenWithoutFacilityClaims() {
        // Create a User
        User user = User.builder()
                .username("testuser")
                .password("password")
                .fullName("Test User")
                .role(Role.EMPLOYEE)
                .enabled(true)
                .build();

        // Create token manually WITHOUT facility claims (old format)
        Map<String, Object> claims = new HashMap<>();
        claims.put("role", "ROLE_" + user.getRole().name());
        // NOT adding: facilityType, facilityId, facilityCode

        Key signingKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(secretKey));

        String token = Jwts.builder()
                .setClaims(claims)
                .setSubject(user.getUsername())
                .setIssuedAt(new Date(System.currentTimeMillis()))
                .setExpiration(new Date(System.currentTimeMillis() + jwtExpiration))
                .signWith(signingKey, SignatureAlgorithm.HS256)
                .compact();

        // Verify token is valid
        assertThat(jwtService.isTokenValid(token, user)).isTrue();
        assertThat(jwtService.extractUsername(token)).isEqualTo("testuser");

        // Verify facility claims are null (not present)
        assertThat(jwtService.getFacilityType(token)).isNull();
        assertThat(jwtService.getFacilityId(token)).isNull();
        assertThat(jwtService.getFacilityCode(token)).isNull();
    }

    @Test
    @DisplayName("Should generate token without facility claims when repository is null")
    void shouldGenerateTokenWithoutFacilityClaimsWhenRepositoryNull() {
        // Create a User WITHOUT facility info
        User user = User.builder()
                .username("employee")
                .password("password")
                .fullName("Employee User")
                .role(Role.EMPLOYEE)
                .enabled(true)
                .build();

        // Generate token (facilityRepository is null)
        String token = jwtService.generateToken(user);

        // Verify token is valid
        assertThat(token).isNotNull();
        assertThat(jwtService.isTokenValid(token, user)).isTrue();
        assertThat(jwtService.extractUsername(token)).isEqualTo("employee");

        // Verify no facility claims
        assertThat(jwtService.getFacilityType(token)).isNull();
        assertThat(jwtService.getFacilityId(token)).isNull();
        assertThat(jwtService.getFacilityCode(token)).isNull();
    }

    @Test
    @DisplayName("Should extract username from token")
    void shouldExtractUsername() {
        User user = User.builder()
                .username("admin")
                .password("password")
                .fullName("Admin User")
                .role(Role.ADMIN)
                .enabled(true)
                .build();

        String token = jwtService.generateToken(user);

        assertThat(jwtService.extractUsername(token)).isEqualTo("admin");
    }

    @Test
    @DisplayName("Should validate token successfully")
    void shouldValidateToken() {
        User user = User.builder()
                .username("manager")
                .password("password")
                .fullName("Manager User")
                .role(Role.MANAGER)
                .enabled(true)
                .build();

        String token = jwtService.generateToken(user);

        assertThat(jwtService.isTokenValid(token, user)).isTrue();
    }

    @Test
    @DisplayName("Should reject expired token")
    void shouldRejectExpiredToken() {
        User user = User.builder()
                .username("testuser")
                .password("password")
                .fullName("Test User")
                .role(Role.EMPLOYEE)
                .enabled(true)
                .build();

        // Create expired token
        Map<String, Object> claims = new HashMap<>();
        claims.put("role", "ROLE_EMPLOYEE");

        Key signingKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(secretKey));

        String expiredToken = Jwts.builder()
                .setClaims(claims)
                .setSubject(user.getUsername())
                .setIssuedAt(new Date(System.currentTimeMillis() - 7200000)) // 2 hours ago
                .setExpiration(new Date(System.currentTimeMillis() - 3600000)) // 1 hour ago (expired)
                .signWith(signingKey, SignatureAlgorithm.HS256)
                .compact();

        // Token validation throws exception for expired tokens
        try {
            jwtService.isTokenValid(expiredToken, user);
            // If no exception, the test should fail
            assertThat(false).as("Expected token validation to throw exception for expired token").isTrue();
        } catch (io.jsonwebtoken.ExpiredJwtException e) {
            // Expected - token is expired
            assertThat(e).isNotNull();
        }
    }
}
