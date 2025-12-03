-- WH-270: Stock table for multi-facility inventory

-- Создаём таблицу stock
CREATE TABLE stock (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    facility_id BIGINT NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Один товар может быть только один раз на одном объекте
    CONSTRAINT uk_stock_product_facility UNIQUE (product_id, facility_id),

    -- quantity и reserved не могут быть отрицательными
    CONSTRAINT chk_stock_quantity CHECK (quantity >= 0),
    CONSTRAINT chk_stock_reserved CHECK (reserved >= 0),
    CONSTRAINT chk_stock_available CHECK (quantity >= reserved)
);

-- Индексы для быстрого поиска
CREATE INDEX idx_stock_product_id ON stock(product_id);
CREATE INDEX idx_stock_facility_id ON stock(facility_id);
CREATE INDEX idx_stock_quantity ON stock(quantity) WHERE quantity > 0;

-- Комментарии
COMMENT ON TABLE stock IS 'Остатки товаров на объектах (WH-270)';
COMMENT ON COLUMN stock.quantity IS 'Общее количество на объекте';
COMMENT ON COLUMN stock.reserved IS 'Зарезервировано (в процессе отгрузки)';

-- Миграция данных: переносим quantity из products в stock
-- Используем первый DC как дефолтный объект для существующих товаров
INSERT INTO stock (product_id, facility_id, quantity, reserved, created_at, updated_at)
SELECT
    p.id,
    (SELECT id FROM facilities WHERE type = 'DC' ORDER BY id LIMIT 1),
    COALESCE(p.quantity, 0),
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM products p
WHERE p.quantity IS NOT NULL AND p.quantity > 0
  AND EXISTS (SELECT 1 FROM facilities WHERE type = 'DC');

-- НЕ удаляем quantity из products пока — это будет в отдельной миграции V5
-- после того как убедимся что всё работает
