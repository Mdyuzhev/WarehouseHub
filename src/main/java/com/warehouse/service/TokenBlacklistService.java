package com.warehouse.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Date;

/**
 * JWT Token Blacklist Service using Redis.
 * Allows invalidating tokens on logout.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class TokenBlacklistService {

    private final RedisTemplate<String, Object> redisTemplate;

    private static final String BLACKLIST_PREFIX = "jwt_blacklist:";

    /**
     * Add token to blacklist.
     * Token will be automatically removed when it would have expired anyway.
     *
     * @param token JWT token to blacklist
     * @param expirationDate token's original expiration date
     */
    public void blacklistToken(String token, Date expirationDate) {
        String key = BLACKLIST_PREFIX + token;
        long ttlMillis = expirationDate.getTime() - System.currentTimeMillis();

        if (ttlMillis > 0) {
            redisTemplate.opsForValue().set(key, "blacklisted", Duration.ofMillis(ttlMillis));
            log.info("Token blacklisted, TTL: {} seconds", ttlMillis / 1000);
        }
    }

    /**
     * Check if token is blacklisted.
     *
     * @param token JWT token to check
     * @return true if token is blacklisted
     */
    public boolean isBlacklisted(String token) {
        String key = BLACKLIST_PREFIX + token;
        return Boolean.TRUE.equals(redisTemplate.hasKey(key));
    }
}
