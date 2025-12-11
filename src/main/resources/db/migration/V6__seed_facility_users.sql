-- WH-271.2: Seed facility users (7 operators)

-- dc_manager (MANAGER role for DC)
INSERT INTO users (username, password, email, full_name, role, enabled, facility_type, facility_id) VALUES
('dc_manager', '$2a$10$N9qo8uLOickgx2ZMRZoMye.Yjhx/G8SWRuT8KW6UTZiwKfFwF6Q.i', 'dc_manager@warehouse.local', 'Менеджер РЦ', 'MANAGER', true, 'DC', 1);

-- wh_north_op (EMPLOYEE role for WH-C-001)
INSERT INTO users (username, password, email, full_name, role, enabled, facility_type, facility_id) VALUES
('wh_north_op', '$2a$10$N9qo8uLOickgx2ZMRZoMye.Yjhx/G8SWRuT8KW6UTZiwKfFwF6Q.i', 'wh_north_op@warehouse.local', 'Оператор Север', 'EMPLOYEE', true, 'WH', 2);

-- wh_south_op (EMPLOYEE role for WH-C-002)
INSERT INTO users (username, password, email, full_name, role, enabled, facility_type, facility_id) VALUES
('wh_south_op', '$2a$10$N9qo8uLOickgx2ZMRZoMye.Yjhx/G8SWRuT8KW6UTZiwKfFwF6Q.i', 'wh_south_op@warehouse.local', 'Оператор Юг', 'EMPLOYEE', true, 'WH', 3);

-- pp_1_op (EMPLOYEE role for PP-C-001)
INSERT INTO users (username, password, email, full_name, role, enabled, facility_type, facility_id) VALUES
('pp_1_op', '$2a$10$N9qo8uLOickgx2ZMRZoMye.Yjhx/G8SWRuT8KW6UTZiwKfFwF6Q.i', 'pp_1_op@warehouse.local', 'Оператор ПВЗ 1', 'EMPLOYEE', true, 'PP', 4);

-- pp_2_op (EMPLOYEE role for PP-C-002)
INSERT INTO users (username, password, email, full_name, role, enabled, facility_type, facility_id) VALUES
('pp_2_op', '$2a$10$N9qo8uLOickgx2ZMRZoMye.Yjhx/G8SWRuT8KW6UTZiwKfFwF6Q.i', 'pp_2_op@warehouse.local', 'Оператор ПВЗ 2', 'EMPLOYEE', true, 'PP', 5);

-- pp_3_op (EMPLOYEE role for PP-C-003)
INSERT INTO users (username, password, email, full_name, role, enabled, facility_type, facility_id) VALUES
('pp_3_op', '$2a$10$N9qo8uLOickgx2ZMRZoMye.Yjhx/G8SWRuT8KW6UTZiwKfFwF6Q.i', 'pp_3_op@warehouse.local', 'Оператор ПВЗ 3', 'EMPLOYEE', true, 'PP', 6);

-- pp_4_op (EMPLOYEE role for PP-C-004)
INSERT INTO users (username, password, email, full_name, role, enabled, facility_type, facility_id) VALUES
('pp_4_op', '$2a$10$N9qo8uLOickgx2ZMRZoMye.Yjhx/G8SWRuT8KW6UTZiwKfFwF6Q.i', 'pp_4_op@warehouse.local', 'Оператор ПВЗ 4', 'EMPLOYEE', true, 'PP', 7);
