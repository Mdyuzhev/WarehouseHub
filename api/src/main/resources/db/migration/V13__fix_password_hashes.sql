-- WH-FIX: Fix bcrypt password hashes (use $2a$ format compatible with Java BCryptPasswordEncoder)
-- Previous hashes used $2b$ which caused authentication failures

-- admin (password: admin123)
UPDATE users SET password = '$2a$10$W3WBsXHZq59RzTaQWngo6e0tDONRmsN0E0DYtVv/B0t4r7NWq4.rq' WHERE username = 'admin';

-- All other users (password: password123)
UPDATE users SET password = '$2a$10$Qiz0YvUQfERNVk817oMXhOEaMUQY3EoILQxLCswzNDVqOJ2rpYyp.' WHERE username <> 'admin';
