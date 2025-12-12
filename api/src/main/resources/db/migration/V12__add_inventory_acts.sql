-- V12: Inventory Acts - инвентаризация складских остатков
-- WH-275: Блок 3
-- Stock correction based on expected vs actual quantities

CREATE TABLE inventory_acts (
    id BIGSERIAL PRIMARY KEY,
    document_number VARCHAR(50) UNIQUE NOT NULL,

    -- Facility (любой склад/ПВЗ)
    facility_id BIGINT NOT NULL REFERENCES facilities(id),

    -- Status: DRAFT → COMPLETED
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',

    -- Notes
    notes TEXT,

    -- Audit fields
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_by BIGINT REFERENCES users(id),
    completed_at TIMESTAMP
);

CREATE TABLE inventory_act_items (
    id BIGSERIAL PRIMARY KEY,
    inventory_act_id BIGINT NOT NULL REFERENCES inventory_acts(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id),

    -- Expected quantity (from system stock)
    expected_quantity INTEGER NOT NULL DEFAULT 0,

    -- Actual quantity (counted during inventory)
    actual_quantity INTEGER NOT NULL DEFAULT 0,

    -- Difference (calculated: actual - expected)
    difference INTEGER GENERATED ALWAYS AS (actual_quantity - expected_quantity) STORED
);

-- Indexes
CREATE INDEX idx_inventory_acts_facility ON inventory_acts(facility_id);
CREATE INDEX idx_inventory_acts_created_at ON inventory_acts(created_at);
CREATE INDEX idx_inventory_acts_status ON inventory_acts(status);
CREATE INDEX idx_inventory_act_items_inventory_act ON inventory_act_items(inventory_act_id);
CREATE INDEX idx_inventory_act_items_product ON inventory_act_items(product_id);

-- Comments
COMMENT ON TABLE inventory_acts IS 'Акты инвентаризации складских остатков';
COMMENT ON TABLE inventory_act_items IS 'Позиции актов инвентаризации';
COMMENT ON COLUMN inventory_acts.document_number IS 'Формат: INV-{facilityCode}-{YYYYMMDD}-{seq}';
COMMENT ON COLUMN inventory_acts.status IS 'DRAFT или COMPLETED (stock correction applied)';
COMMENT ON COLUMN inventory_act_items.expected_quantity IS 'Ожидаемое количество (из системы)';
COMMENT ON COLUMN inventory_act_items.actual_quantity IS 'Фактическое количество (посчитанное)';
COMMENT ON COLUMN inventory_act_items.difference IS 'Разница (фактическое - ожидаемое)';
