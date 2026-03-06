-- =============================================================================
-- Migration V1: Initial schema - users and products tables
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    role VARCHAR(20) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    description VARCHAR(100),
    category VARCHAR(50)
);

-- Seed admin user (password: admin123 encoded with bcrypt)
INSERT INTO users (username, password, full_name, email, role, enabled)
VALUES ('admin', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 'Administrator', 'admin@warehouse.com', 'SUPER_USER', true)
ON CONFLICT (username) DO NOTHING;

-- Seed products
INSERT INTO products (name, quantity, price, description, category) VALUES
('Laptop', 0, 999.99, 'High-performance laptop', 'Electronics'),
('Mouse', 0, 29.99, 'Wireless mouse', 'Electronics'),
('Keyboard', 0, 49.99, 'Mechanical keyboard', 'Electronics'),
('Monitor', 0, 399.99, '27-inch 4K monitor', 'Electronics'),
('Headphones', 0, 79.99, 'Noise-cancelling headphones', 'Electronics');
