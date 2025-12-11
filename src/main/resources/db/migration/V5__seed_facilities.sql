-- WH-271.1: Seed test hierarchy DC → WH → PP

-- 7 тестовых facilities для иерархии
INSERT INTO facilities (id, type, code, name, address, parent_id, created_at) VALUES
-- DC (Root)
(1, 'DC', 'DC-C-001', 'Центральный РЦ', 'г. Москва, ул. Складская, д. 1', NULL, CURRENT_TIMESTAMP),

-- Warehouses (Level 2)
(2, 'WH', 'WH-C-001', 'Склад Север', 'г. Москва, ул. Северная, д. 10', 1, CURRENT_TIMESTAMP),
(3, 'WH', 'WH-C-002', 'Склад Юг', 'г. Москва, ул. Южная, д. 20', 1, CURRENT_TIMESTAMP),

-- Pickup Points (Level 3)
(4, 'PP', 'PP-C-001', 'ПВЗ 1', 'г. Москва, ул. Ленина, д. 1', 2, CURRENT_TIMESTAMP),
(5, 'PP', 'PP-C-002', 'ПВЗ 2', 'г. Москва, ул. Ленина, д. 2', 2, CURRENT_TIMESTAMP),
(6, 'PP', 'PP-C-003', 'ПВЗ 3', 'г. Москва, ул. Пушкина, д. 1', 3, CURRENT_TIMESTAMP),
(7, 'PP', 'PP-C-004', 'ПВЗ 4', 'г. Москва, ул. Пушкина, д. 2', 3, CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;

-- Обновляем sequence для id
SELECT setval('facilities_id_seq', (SELECT MAX(id) FROM facilities));

-- Комментарии
COMMENT ON TABLE facilities IS 'Test hierarchy: 1 DC → 2 WH → 4 PP (WH-271)';
