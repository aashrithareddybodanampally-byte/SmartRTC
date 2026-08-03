-- SmartRTC Sample Data Generator
-- Run after schema.sql

-- Users
INSERT INTO users (username, password_hash, role, full_name) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G2qTqR5E2Y5K2i', 'admin', 'System Admin'),
('planner', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G2qTqR5E2Y5K2i', 'planner', 'Route Planner'),
('viewer', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G2qTqR5E2Y5K2i', 'viewer', 'Viewer')
ON CONFLICT (username) DO NOTHING;

-- Buses
INSERT INTO buses (bus_number, capacity, bus_type, status) VALUES
('100', 50, 'standard', 'active'),
('49M', 50, 'standard', 'active'),
('5K', 35, 'mini', 'active'),
('290U', 50, 'standard', 'active')
ON CONFLICT (bus_number) DO NOTHING;

-- Drivers
INSERT INTO drivers (employee_id, full_name, phone, rating, status) VALUES
('D001', 'Rajesh Kumar', '9876543210', 4.5, 'active'),
('D002', 'Suresh Reddy', '9876543211', 4.3, 'active'),
('D003', 'Venkat Rao', '9876543212', 4.8, 'active')
ON CONFLICT (employee_id) DO NOTHING;

-- Conductors
INSERT INTO conductors (employee_id, full_name, phone, rating, status) VALUES
('C001', 'Lakshmi Devi', '9876543220', 4.7, 'active'),
('C002', 'Priya Sharma', '9876543221', 4.6, 'active'),
('C003', 'Manjula Bai', '9876543222', 4.4, 'active')
ON CONFLICT (employee_id) DO NOTHING;

-- Routes and Stops (simplified: route as from_stop -> to_stop)
INSERT INTO routes (route_code, name, distance_km, estimated_duration_min, status) VALUES
('R1', 'Secunderabad → Koti', 12.5, 45, 'active'),
('R2', 'KPHB → Ameerpet', 8.0, 35, 'active'),
('R3', 'Dilsukhnagar → Charminar', 6.0, 25, 'active'),
('R4', 'Uppal → LB Nagar', 10.0, 40, 'active')
ON CONFLICT (route_code) DO NOTHING;

-- Duty roster (today)
INSERT INTO duty_roster (bus_id, driver_id, conductor_id, route_id, duty_date, shift_start, shift_end, status)
SELECT b.id, d.id, c.id, r.id, CURRENT_DATE, '06:00', '14:00', 'scheduled'
FROM buses b
JOIN drivers d ON d.employee_id = CASE b.bus_number WHEN '100' THEN 'D001' WHEN '49M' THEN 'D002' WHEN '5K' THEN 'D003' ELSE 'D001' END
JOIN conductors c ON c.employee_id = CASE b.bus_number WHEN '100' THEN 'C001' WHEN '49M' THEN 'C002' WHEN '5K' THEN 'C003' ELSE 'C001' END
JOIN routes r ON r.id = 1
WHERE b.bus_number IN ('100','49M','5K')
ON CONFLICT DO NOTHING;
