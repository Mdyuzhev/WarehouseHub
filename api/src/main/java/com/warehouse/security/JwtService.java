package com.warehouse.security;

import com.warehouse.model.User;
import com.warehouse.repository.FacilityRepository;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import java.security.Key;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

@Service
public class JwtService {

    private final FacilityRepository facilityRepository;

    @Value("${jwt.secret:bXlTdXBlclNlY3JldEtleUZvckpXVFRva2VuR2VuZXJhdGlvbjEyMzQ1Njc4OTA=}")
    private String secretKey;

    @Value("${jwt.expiration:86400000}")
    private long jwtExpiration;

    // Constructor with optional FacilityRepository injection
    public JwtService(@Autowired(required = false) FacilityRepository facilityRepository) {
        this.facilityRepository = facilityRepository;
    }

    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }

    public String generateToken(UserDetails userDetails) {
        Map<String, Object> extraClaims = new HashMap<>();
        extraClaims.put("role", userDetails.getAuthorities().iterator().next().getAuthority());

        // Add facility claims if user has facility assignment
        if (userDetails instanceof User) {
            User user = (User) userDetails;
            if (user.getFacilityType() != null) {
                extraClaims.put("facilityType", user.getFacilityType().name());
                extraClaims.put("facilityId", user.getFacilityId());

                // Add facility code if facilityId exists and repository is available
                if (user.getFacilityId() != null && facilityRepository != null) {
                    facilityRepository.findById(user.getFacilityId())
                            .ifPresent(facility -> extraClaims.put("facilityCode", facility.getCode()));
                }
            }
        }

        return generateToken(extraClaims, userDetails);
    }

    /**
     * Extract facility type from token
     */
    public String getFacilityType(String token) {
        Claims claims = extractAllClaims(token);
        return claims.get("facilityType", String.class);
    }

    /**
     * Extract facility ID from token
     */
    public Long getFacilityId(String token) {
        Claims claims = extractAllClaims(token);
        Object facilityId = claims.get("facilityId");
        return facilityId != null ? ((Number) facilityId).longValue() : null;
    }

    /**
     * Extract facility code from token
     */
    public String getFacilityCode(String token) {
        Claims claims = extractAllClaims(token);
        return claims.get("facilityCode", String.class);
    }

    public String generateToken(Map<String, Object> extraClaims, UserDetails userDetails) {
        return Jwts.builder()
                .setClaims(extraClaims)
                .setSubject(userDetails.getUsername())
                .setIssuedAt(new Date(System.currentTimeMillis()))
                .setExpiration(new Date(System.currentTimeMillis() + jwtExpiration))
                .signWith(getSignInKey(), SignatureAlgorithm.HS256)
                .compact();
    }

    public boolean isTokenValid(String token, UserDetails userDetails) {
        final String username = extractUsername(token);
        return (username.equals(userDetails.getUsername())) && !isTokenExpired(token);
    }

    private boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }

    public Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    private Claims extractAllClaims(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(getSignInKey())
                .build()
                .parseClaimsJws(token)
                .getBody();
    }

    private Key getSignInKey() {
        byte[] keyBytes = Decoders.BASE64.decode(secretKey);
        return Keys.hmacShaKeyFor(keyBytes);
    }
}
