package com.warehouse.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Date;

/**
 * JWT Token Blacklist Service using Redis.
 * Allows invalidating tokens on logout.
 * Опциональный - работает только если Redis доступен.
 */
@Service
@ConditionalOnBean(RedisTemplate.class)
@Slf4j
public class TokenBlacklistService {

    private final RedisTemplate<String, Object> redisTemplate;

    @Autowired
    public TokenBlacklistService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
        log.info("TokenBlacklistService initialized with Redis");
    }

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
