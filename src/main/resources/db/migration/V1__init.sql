-- WH-000: Initial schema and seed data

-- Create users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL CHECK (role IN ('SUPER_USER', 'ADMIN', 'MANAGER', 'EMPLOYEE')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    facility_type VARCHAR(10),
    facility_id BIGINT
);

COMMENT ON COLUMN users.facility_type IS 'Тип объекта, к которому привязан пользователь (null для SUPER_USER)';
COMMENT ON COLUMN users.facility_id IS 'ID объекта, к которому привязан пользователь (null для SUPER_USER)';

CREATE INDEX idx_users_facility_type ON users(facility_type);
CREATE INDEX idx_users_facility_id ON users(facility_id);

-- Create products table
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255),
    description VARCHAR(100),
    price DOUBLE PRECISION,
    quantity INTEGER,
    category VARCHAR(50)
);

-- Seed admin user (password: admin123)
INSERT INTO users (username, password, email, full_name, role, enabled, facility_type, facility_id) VALUES
('admin', '$2b$12$LxW.y39.WTA2kZK.8l7X5eaa1Agf2.e.fr/tFY2/0i6g/3dhxsCXi', 'admin@warehouse.local', 'System Administrator', 'SUPER_USER', true, NULL, NULL);

-- Seed employee user (password: password123)
INSERT INTO users (username, password, email, full_name, role, enabled, facility_type, facility_id) VALUES
('employee', '$2b$12$LxW.y39.WTA2kZK.8l7X5eaa1Agf2.e.fr/tFY2/0i6g/3dhxsCXi', 'employee@warehouse.local', 'Test Employee', 'EMPLOYEE', true, NULL, NULL);

-- Seed test products
INSERT INTO products (name, description, price, quantity, category) VALUES
('Laptop', 'High performance laptop', 999.99, 10, 'Electronics'),
('Mouse', 'Wireless mouse', 29.99, 50, 'Electronics'),
('Keyboard', 'Mechanical keyboard', 79.99, 30, 'Electronics'),
('Monitor', '27 inch 4K monitor', 399.99, 15, 'Electronics'),
('Headphones', 'Noise-cancelling headphones', 149.99, 25, 'Electronics');
