-- WH-271.3: Seed stock records for test hierarchy

-- WH-C-001 (facility_id=2): 5 products
INSERT INTO stock (product_id, facility_id, quantity, reserved) VALUES
(1, 2, 150, 0),  -- Laptop
(2, 2, 200, 0),  -- Mouse
(3, 2, 120, 0),  -- Keyboard
(4, 2, 80, 0),   -- Monitor
(5, 2, 100, 0);  -- Headphones

-- WH-C-002 (facility_id=3): 5 products
INSERT INTO stock (product_id, facility_id, quantity, reserved) VALUES
(1, 3, 180, 0),  -- Laptop
(2, 3, 190, 0),  -- Mouse
(3, 3, 140, 0),  -- Keyboard
(4, 3, 90, 0),   -- Monitor
(5, 3, 110, 0);  -- Headphones

-- PP-C-001 (facility_id=4): 3 products
INSERT INTO stock (product_id, facility_id, quantity, reserved) VALUES
(1, 4, 25, 0),   -- Laptop
(2, 4, 50, 0),   -- Mouse
(3, 4, 35, 0);   -- Keyboard

-- PP-C-002 (facility_id=5): 3 products
INSERT INTO stock (product_id, facility_id, quantity, reserved) VALUES
(1, 5, 30, 0),   -- Laptop
(2, 5, 45, 0),   -- Mouse
(3, 5, 40, 0);   -- Keyboard

-- PP-C-003 (facility_id=6): 3 products
INSERT INTO stock (product_id, facility_id, quantity, reserved) VALUES
(1, 6, 20, 0),   -- Laptop
(2, 6, 48, 0),   -- Mouse
(3, 6, 32, 0);   -- Keyboard

-- PP-C-004 (facility_id=7): 3 products
INSERT INTO stock (product_id, facility_id, quantity, reserved) VALUES
(1, 7, 28, 0),   -- Laptop
(2, 7, 42, 0),   -- Mouse
(3, 7, 38, 0);   -- Keyboard

-- Note: DC-C-001 (facility_id=1) не имеет stock — это распределительный центр
