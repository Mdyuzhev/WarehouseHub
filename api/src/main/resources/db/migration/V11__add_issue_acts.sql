-- V11: Issue Acts - выдача товара клиентам в ПВЗ
-- WH-275: Блок 1
-- Только для pickup points (PP), instant stock deduction при COMPLETED

CREATE TABLE issue_acts (
    id BIGSERIAL PRIMARY KEY,
    document_number VARCHAR(50) UNIQUE NOT NULL,

    -- Facility (только PP!)
    facility_id BIGINT NOT NULL REFERENCES facilities(id),

    -- Customer info
    customer_name VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(50),

    -- Status: DRAFT → COMPLETED
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',

    -- Notes
    notes TEXT,

    -- Audit fields
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP

    -- Note: facility_type=PP validation in IssueActService
);

CREATE TABLE issue_act_items (
    id BIGSERIAL PRIMARY KEY,
    issue_act_id BIGINT NOT NULL REFERENCES issue_acts(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);

-- Indexes
CREATE INDEX idx_issue_acts_facility ON issue_acts(facility_id);
CREATE INDEX idx_issue_acts_created_at ON issue_acts(created_at);
CREATE INDEX idx_issue_acts_status ON issue_acts(status);
CREATE INDEX idx_issue_act_items_issue_act ON issue_act_items(issue_act_id);
CREATE INDEX idx_issue_act_items_product ON issue_act_items(product_id);

-- Comments
COMMENT ON TABLE issue_acts IS 'Акты выдачи товара клиентам (только для ПВЗ)';
COMMENT ON TABLE issue_act_items IS 'Позиции актов выдачи';
COMMENT ON COLUMN issue_acts.document_number IS 'Формат: ISS-{facilityCode}-{YYYYMMDD}-{seq}';
COMMENT ON COLUMN issue_acts.status IS 'DRAFT или COMPLETED (instant stock deduction)';
