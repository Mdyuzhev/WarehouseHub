-- V10: Link Receipt to Shipment for Kafka Auto-Documents
-- WH-274: Блок 1
-- When shipment is SHIPPED → auto-create receipt on destination facility

-- Add source_shipment_id to receipt_documents
ALTER TABLE receipt_documents
    ADD COLUMN source_shipment_id BIGINT;

ALTER TABLE receipt_documents
    ADD CONSTRAINT fk_receipt_source_shipment
    FOREIGN KEY (source_shipment_id)
    REFERENCES shipment_documents(id)
    ON DELETE SET NULL;

-- Index for faster lookups
CREATE INDEX idx_receipt_source_shipment
    ON receipt_documents(source_shipment_id);

COMMENT ON COLUMN receipt_documents.source_shipment_id IS 'Reference to originating shipment (for auto-created receipts)';
