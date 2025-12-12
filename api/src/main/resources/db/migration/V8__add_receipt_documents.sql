-- WH-272: Receipt Documents (Приходные накладные)
-- Блок 1: Entity + Migration

-- Таблица receipt_documents
CREATE TABLE receipt_documents (
    id BIGSERIAL PRIMARY KEY,
    document_number VARCHAR(50) NOT NULL UNIQUE,
    facility_id BIGINT NOT NULL REFERENCES facilities(id),
    supplier_name VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    notes TEXT,
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by BIGINT REFERENCES users(id),
    confirmed_at TIMESTAMP,
    confirmed_by BIGINT REFERENCES users(id)
);

COMMENT ON TABLE receipt_documents IS 'Приходные накладные';
COMMENT ON COLUMN receipt_documents.document_number IS 'Формат: RCP-{facilityCode}-{YYYYMMDD}-{seq}';
COMMENT ON COLUMN receipt_documents.status IS 'DRAFT, APPROVED, CONFIRMED, COMPLETED';

CREATE INDEX idx_receipt_documents_facility_id ON receipt_documents(facility_id);
CREATE INDEX idx_receipt_documents_status ON receipt_documents(status);
CREATE INDEX idx_receipt_documents_created_at ON receipt_documents(created_at);

-- Таблица receipt_items
CREATE TABLE receipt_items (
    id BIGSERIAL PRIMARY KEY,
    receipt_id BIGINT NOT NULL REFERENCES receipt_documents(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id),
    expected_quantity INTEGER NOT NULL CHECK (expected_quantity > 0),
    actual_quantity INTEGER DEFAULT 0 CHECK (actual_quantity >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE receipt_items IS 'Позиции приходной накладной';
COMMENT ON COLUMN receipt_items.expected_quantity IS 'Ожидаемое количество';
COMMENT ON COLUMN receipt_items.actual_quantity IS 'Фактически принятое количество';

CREATE INDEX idx_receipt_items_receipt_id ON receipt_items(receipt_id);
CREATE INDEX idx_receipt_items_product_id ON receipt_items(product_id);
