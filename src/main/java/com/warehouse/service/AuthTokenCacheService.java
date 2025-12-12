package com.warehouse.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

/**
 * Auth Token Cache Service using Redis.
 *
 * Кэширует JWT токены для снижения нагрузки BCrypt при повторных логинах.
 *
 * БЕЗОПАСНОСТЬ: Кэш-ключ включает hash пароля, поэтому:
 * - Разные пароли = разные ключи = cache miss
 * - При смене пароля старый кэш автоматически не используется
 *
 * TTL: 1 час (3600 секунд) - токен автоматически удаляется из кэша
 */
@Service
@ConditionalOnBean(RedisTemplate.class)
@Slf4j
public class AuthTokenCacheService {

    private final RedisTemplate<String, Object> redisTemplate;

    private static final String CACHE_PREFIX = "auth:token:";
    private static final long DEFAULT_TTL_SECONDS = 3600; // 1 час

    @Autowired
    public AuthTokenCacheService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
        log.info("AuthTokenCacheService initialized with Redis");
    }

    /**
     * Генерирует безопасный ключ кэша.
     * Включает hash пароля для защиты от атак без пароля.
     *
     * @param username имя пользователя
     * @param passwordHash первые 16 символов закодированного пароля из БД
     * @return ключ для Redis
     */
    private String buildCacheKey(String username, String passwordHash) {
        // Используем первые 16 символов BCrypt hash как "соль" ключа
        // Это безопасно - BCrypt hash уже содержит соль и не раскрывает пароль
        String hashPart = passwordHash != null && passwordHash.length() >= 16
            ? passwordHash.substring(0, 16)
            : "default";
        return CACHE_PREFIX + username + ":" + hashPart.hashCode();
    }

    /**
     * Получить токен из кэша.
     *
     * @param username имя пользователя
     * @param passwordHash BCrypt hash пароля из БД (для валидации)
     * @return токен или null если не найден / ошибка Redis
     */
    public String getCachedToken(String username, String passwordHash) {
        try {
            String key = buildCacheKey(username, passwordHash);
            Object value = redisTemplate.opsForValue().get(key);
            if (value != null) {
                log.debug("Cache HIT for user: {}", username);
                return value.toString();
            }
            log.debug("Cache MISS for user: {}", username);
            return null;
        } catch (Exception e) {
            log.warn("Redis error on getCachedToken: {}", e.getMessage());
            return null; // Graceful fallback - продолжаем без кэша
        }
    }

    /**
     * Сохранить токен в кэш.
     *
     * @param username имя пользователя
     * @param passwordHash BCrypt hash пароля из БД
     * @param token JWT токен для кэширования
     */
    public void cacheToken(String username, String passwordHash, String token) {
        try {
            String key = buildCacheKey(username, passwordHash);
            redisTemplate.opsForValue().set(key, token, DEFAULT_TTL_SECONDS, TimeUnit.SECONDS);
            log.debug("Token cached for user: {}, TTL: {}s", username, DEFAULT_TTL_SECONDS);
        } catch (Exception e) {
            log.warn("Redis error on cacheToken: {}", e.getMessage());
            // Не фейлим логин если Redis недоступен
        }
    }

    /**
     * Сохранить токен с кастомным TTL.
     *
     * @param username имя пользователя
     * @param passwordHash BCrypt hash пароля из БД
     * @param token JWT токен
     * @param ttlSeconds время жизни в секундах
     */
    public void cacheToken(String username, String passwordHash, String token, long ttlSeconds) {
        try {
            String key = buildCacheKey(username, passwordHash);
            redisTemplate.opsForValue().set(key, token, ttlSeconds, TimeUnit.SECONDS);
            log.debug("Token cached for user: {}, TTL: {}s", username, ttlSeconds);
        } catch (Exception e) {
            log.warn("Redis error on cacheToken: {}", e.getMessage());
        }
    }

    /**
     * Инвалидировать токен (удалить из кэша).
     * Вызывается при logout или смене пароля.
     *
     * @param username имя пользователя
     * @param passwordHash BCrypt hash пароля
     */
    public void invalidateToken(String username, String passwordHash) {
        try {
            String key = buildCacheKey(username, passwordHash);
            Boolean deleted = redisTemplate.delete(key);
            log.debug("Token invalidated for user: {}, deleted: {}", username, deleted);
        } catch (Exception e) {
            log.warn("Redis error on invalidateToken: {}", e.getMessage());
        }
    }

    /**
     * Проверить доступность Redis.
     *
     * @return true если Redis работает
     */
    public boolean isAvailable() {
        try {
            redisTemplate.getConnectionFactory().getConnection().ping();
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
