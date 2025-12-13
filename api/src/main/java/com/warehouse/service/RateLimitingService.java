package com.warehouse.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;

/**
 * Rate Limiting Service using Redis.
 * Protects endpoints from brute force attacks.
 * Опциональный - работает только если Redis доступен.
 */
@Service
@ConditionalOnBean(RedisTemplate.class)
@Slf4j
public class RateLimitingService {

    private final RedisTemplate<String, Object> redisTemplate;

    @Autowired
    public RateLimitingService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
        log.info("RateLimitingService initialized with Redis");
    }

    private static final String RATE_LIMIT_PREFIX = "rate_limit:";

    @Value("${rate-limit.login.max-attempts:5}")
    private int maxLoginAttempts;

    @Value("${rate-limit.login.window-minutes:15}")
    private int windowMinutes;

    /**
     * Check if login attempt is allowed for given identifier (username or IP).
     * @param identifier username or IP address
     * @return true if attempt is allowed, false if rate limited
     */
    public boolean isLoginAllowed(String identifier) {
        String key = RATE_LIMIT_PREFIX + "login:" + identifier;
        Long attempts = redisTemplate.opsForValue().increment(key);

        if (attempts == null) {
            return true;
        }

        if (attempts == 1) {
            redisTemplate.expire(key, java.util.Objects.requireNonNull(Duration.ofMinutes(windowMinutes)));
        }

        boolean allowed = attempts <= maxLoginAttempts;
        if (!allowed) {
            log.warn("Rate limit exceeded for login attempt: {}", identifier);
        }
        return allowed;
    }

    /**
     * Get remaining attempts for identifier.
     * @param identifier username or IP address
     * @return remaining attempts, or max if not limited
     */
    public int getRemainingAttempts(String identifier) {
        String key = RATE_LIMIT_PREFIX + "login:" + identifier;
        Object value = redisTemplate.opsForValue().get(key);
        if (value == null) {
            return maxLoginAttempts;
        }
        int attempts = Integer.parseInt(value.toString());
        return Math.max(0, maxLoginAttempts - attempts);
    }

    /**
     * Reset rate limit for identifier (e.g., after successful login).
     * @param identifier username or IP address
     */
    public void resetLoginAttempts(String identifier) {
        String key = RATE_LIMIT_PREFIX + "login:" + identifier;
        redisTemplate.delete(key);
    }

    /**
     * Get time until rate limit expires in seconds.
     * @param identifier username or IP address
     * @return seconds until limit expires, or 0 if not limited
     */
    public long getTimeUntilReset(String identifier) {
        String key = RATE_LIMIT_PREFIX + "login:" + identifier;
        Long ttl = redisTemplate.getExpire(key);
        return ttl != null && ttl > 0 ? ttl : 0;
    }
}
