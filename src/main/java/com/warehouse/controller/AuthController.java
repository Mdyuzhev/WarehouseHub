package com.warehouse.controller;

import com.warehouse.dto.AuthRequest;
import com.warehouse.dto.AuthResponse;
import com.warehouse.dto.RegisterRequest;
import com.warehouse.model.Role;
import com.warehouse.model.User;
import com.warehouse.repository.UserRepository;
import com.warehouse.security.JwtService;
import com.warehouse.service.RateLimitingService;
import com.warehouse.service.TokenBlacklistService;
import com.warehouse.service.AuthTokenCacheService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final RateLimitingService rateLimitingService;  // nullable если Redis недоступен
    private final TokenBlacklistService tokenBlacklistService;  // nullable если Redis недоступен
    private final AuthTokenCacheService authTokenCacheService;  // nullable если Redis недоступен

    public AuthController(
            @Lazy AuthenticationManager authenticationManager,
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            @Autowired(required = false) RateLimitingService rateLimitingService,
            @Autowired(required = false) TokenBlacklistService tokenBlacklistService,
            @Autowired(required = false) AuthTokenCacheService authTokenCacheService) {
        this.authenticationManager = authenticationManager;
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.rateLimitingService = rateLimitingService;
        this.tokenBlacklistService = tokenBlacklistService;
        this.authTokenCacheService = authTokenCacheService;
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody AuthRequest request, HttpServletRequest httpRequest) {
        String clientIp = getClientIp(httpRequest);
        String rateLimitKey = request.getUsername() + ":" + clientIp;

        // Check rate limit (only if Redis is available)
        if (rateLimitingService != null && !rateLimitingService.isLoginAllowed(rateLimitKey)) {
            long retryAfter = rateLimitingService.getTimeUntilReset(rateLimitKey);
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                    .header("Retry-After", String.valueOf(retryAfter))
                    .body(Map.of(
                            "error", "Too many login attempts. Please try again later.",
                            "retryAfterSeconds", retryAfter
                    ));
        }

        try {
            // Сначала получаем пользователя для проверки кэша
            User user = userRepository.findByUsername(request.getUsername())
                    .orElseThrow(() -> new BadCredentialsException("User not found"));

            // Проверяем кэш токенов (только если Redis доступен)
            // Ключ кэша включает hash пароля, поэтому неверный пароль = cache miss
            if (authTokenCacheService != null) {
                // Проверяем пароль перед использованием кэша
                if (passwordEncoder.matches(request.getPassword(), user.getPassword())) {
                    String cachedToken = authTokenCacheService.getCachedToken(
                            request.getUsername(), user.getPassword());
                    if (cachedToken != null && jwtService.isTokenValid(cachedToken, user)) {
                        // Cache HIT - возвращаем кэшированный токен без BCrypt
                        if (rateLimitingService != null) {
                            rateLimitingService.resetLoginAttempts(rateLimitKey);
                        }
                        return ResponseEntity.ok(AuthResponse.builder()
                                .token(cachedToken)
                                .username(user.getUsername())
                                .fullName(user.getFullName())
                                .role(user.getRole())
                                .build());
                    }
                }
            }

            // Cache MISS или Redis недоступен - стандартная аутентификация
            authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getUsername(), request.getPassword())
            );

            // Reset rate limit on successful login (only if Redis is available)
            if (rateLimitingService != null) {
                rateLimitingService.resetLoginAttempts(rateLimitKey);
            }

            String token = jwtService.generateToken(user);

            // Кэшируем токен для будущих логинов
            if (authTokenCacheService != null) {
                authTokenCacheService.cacheToken(request.getUsername(), user.getPassword(), token);
            }

            return ResponseEntity.ok(AuthResponse.builder()
                    .token(token)
                    .username(user.getUsername())
                    .fullName(user.getFullName())
                    .role(user.getRole())
                    .build());

        } catch (BadCredentialsException e) {
            int remaining = rateLimitingService != null ? rateLimitingService.getRemainingAttempts(rateLimitKey) : -1;
            if (remaining >= 0) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(Map.of(
                                "error", "Invalid username or password",
                                "remainingAttempts", remaining
                        ));
            } else {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(Map.of("error", "Invalid username or password"));
            }
        }
    }

    private String getClientIp(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty()) {
            return xForwardedFor.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody RegisterRequest request) {
        if (userRepository.existsByUsername(request.getUsername())) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Username already exists"));
        }

        if (request.getEmail() != null && userRepository.existsByEmail(request.getEmail())) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Email already exists"));
        }

        User user = User.builder()
                .username(request.getUsername())
                .password(passwordEncoder.encode(request.getPassword()))
                .fullName(request.getFullName())
                .email(request.getEmail())
                .role(request.getRole() != null ? request.getRole() : Role.EMPLOYEE)
                .enabled(true)
                .build();

        userRepository.save(user);

        return ResponseEntity.status(HttpStatus.CREATED)
                .body(Map.of(
                    "message", "User registered successfully",
                    "username", user.getUsername(),
                    "role", user.getRole()
                ));
    }

    @GetMapping("/me")
    public ResponseEntity<?> getCurrentUser(@RequestHeader(value = "Authorization", required = false) String authHeader) {
        if (authHeader == null || !authHeader.startsWith("Bearer ") || authHeader.length() < 8) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Invalid authorization header"));
        }
        try {
            String token = authHeader.substring(7);
            String username = jwtService.extractUsername(token);
            
            User user = userRepository.findByUsername(username)
                    .orElseThrow(() -> new RuntimeException("User not found"));

            return ResponseEntity.ok(AuthResponse.builder()
                    .username(user.getUsername())
                    .fullName(user.getFullName())
                    .role(user.getRole())
                    .build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Invalid token"));
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout(@RequestHeader(value = "Authorization", required = false) String authHeader) {
        if (authHeader == null || !authHeader.startsWith("Bearer ") || authHeader.length() < 8) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "No token provided"));
        }

        try {
            String token = authHeader.substring(7);
            String username = jwtService.extractUsername(token);

            // Инвалидируем кэш токенов (только если Redis доступен)
            if (authTokenCacheService != null && username != null) {
                User user = userRepository.findByUsername(username).orElse(null);
                if (user != null) {
                    authTokenCacheService.invalidateToken(username, user.getPassword());
                }
            }

            // Blacklist token only if Redis is available
            if (tokenBlacklistService != null) {
                java.util.Date expiration = jwtService.extractExpiration(token);
                tokenBlacklistService.blacklistToken(token, expiration);
            }

            return ResponseEntity.ok(Map.of("message", "Logged out successfully"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Invalid token"));
        }
    }
}
