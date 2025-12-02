-- =============================================================================
-- Migration V1: Add Facilities and extend Users table
-- =============================================================================
-- Story: WH-269
-- Tasks: WH-284
-- Description: Create facilities table and add facility_type, facility_id to users
-- =============================================================================

-- Create facilities table
CREATE TABLE IF NOT EXISTS facilities (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    type VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id BIGINT,
    address VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraint: parent_id references facilities(id)
    CONSTRAINT fk_facility_parent FOREIGN KEY (parent_id)
        REFERENCES facilities(id) ON DELETE RESTRICT,

    -- Check constraint: type must be DC, WH, or PP
    CONSTRAINT chk_facility_type CHECK (type IN ('DC', 'WH', 'PP')),

    -- Check constraint: status must be valid
    CONSTRAINT chk_facility_status CHECK (status IN ('ACTIVE', 'INACTIVE', 'CLOSED'))
);

-- Add columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS facility_type VARCHAR(10);
ALTER TABLE users ADD COLUMN IF NOT EXISTS facility_id BIGINT;

-- Add foreign key constraint: users.facility_id references facilities(id)
ALTER TABLE users ADD CONSTRAINT fk_user_facility
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE RESTRICT;

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_facilities_type ON facilities(type);
CREATE INDEX IF NOT EXISTS idx_facilities_parent_id ON facilities(parent_id);
CREATE INDEX IF NOT EXISTS idx_facilities_status ON facilities(status);
CREATE INDEX IF NOT EXISTS idx_facilities_code ON facilities(code);
CREATE INDEX IF NOT EXISTS idx_users_facility_id ON users(facility_id);
CREATE INDEX IF NOT EXISTS idx_users_facility_type ON users(facility_type);

-- Add comments for documentation
COMMENT ON TABLE facilities IS 'Объекты логистической сети: распределительные центры, склады, пункты выдачи';
COMMENT ON COLUMN facilities.code IS 'Уникальный код: DC-XXX, WH-{region}-XXX, PP-{region}-XXX-YY';
COMMENT ON COLUMN facilities.type IS 'Тип объекта: DC (Distribution Center), WH (Warehouse), PP (Pickup Point)';
COMMENT ON COLUMN facilities.parent_id IS 'Иерархия: DC→null, WH→DC.id, PP→WH.id';
COMMENT ON COLUMN users.facility_type IS 'Тип объекта, к которому привязан пользователь (null для SUPER_USER)';
COMMENT ON COLUMN users.facility_id IS 'ID объекта, к которому привязан пользователь (null для SUPER_USER)';
