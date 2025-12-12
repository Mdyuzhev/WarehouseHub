-- WH-273: Shipment Documents (Расходные накладные)
-- Блок 1: Entity + Migration

-- Таблица shipment_documents
CREATE TABLE shipment_documents (
    id BIGSERIAL PRIMARY KEY,
    document_number VARCHAR(50) NOT NULL UNIQUE,
    source_facility_id BIGINT NOT NULL REFERENCES facilities(id),
    destination_facility_id BIGINT REFERENCES facilities(id),
    destination_address VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    notes TEXT,
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_by BIGINT REFERENCES users(id),
    approved_at TIMESTAMP,
    shipped_by BIGINT REFERENCES users(id),
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP
);

COMMENT ON TABLE shipment_documents IS 'Расходные накладные (отгрузка товара)';
COMMENT ON COLUMN shipment_documents.document_number IS 'Формат: SHP-{sourceFacilityCode}-{YYYYMMDD}-{seq}';
COMMENT ON COLUMN shipment_documents.status IS 'DRAFT, APPROVED, SHIPPED, DELIVERED';
COMMENT ON COLUMN shipment_documents.source_facility_id IS 'Откуда отгружается товар';
COMMENT ON COLUMN shipment_documents.destination_facility_id IS 'Куда отгружается (внутри сети)';
COMMENT ON COLUMN shipment_documents.destination_address IS 'Адрес доставки (если внешний клиент)';

CREATE INDEX idx_shipment_documents_source_facility_id ON shipment_documents(source_facility_id);
CREATE INDEX idx_shipment_documents_destination_facility_id ON shipment_documents(destination_facility_id);
CREATE INDEX idx_shipment_documents_status ON shipment_documents(status);
CREATE INDEX idx_shipment_documents_created_at ON shipment_documents(created_at);

-- Таблица shipment_items
CREATE TABLE shipment_items (
    id BIGSERIAL PRIMARY KEY,
    shipment_id BIGINT NOT NULL REFERENCES shipment_documents(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE shipment_items IS 'Позиции расходной накладной';
COMMENT ON COLUMN shipment_items.quantity IS 'Количество отгружаемого товара';

CREATE INDEX idx_shipment_items_shipment_id ON shipment_items(shipment_id);
CREATE INDEX idx_shipment_items_product_id ON shipment_items(product_id);
