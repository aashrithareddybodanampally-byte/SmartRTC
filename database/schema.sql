-- SmartRTC Intelligent Transport Management System
-- Database Schema (PostgreSQL / MySQL compatible)
-- Core tables as specified

-- Users (admin, planner, viewer, driver, conductor)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    full_name VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(20),
    designation VARCHAR(50),
    employee_id VARCHAR(50) UNIQUE,
    id_proof_path VARCHAR(500),
    approval_status VARCHAR(20) DEFAULT 'pending',
    approved_by INT,
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Buses
CREATE TABLE IF NOT EXISTS buses (
    id SERIAL PRIMARY KEY,
    bus_number VARCHAR(20) UNIQUE NOT NULL,
    capacity INT NOT NULL DEFAULT 50,
    bus_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drivers
CREATE TABLE IF NOT EXISTS drivers (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    rating DECIMAL(3,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conductors
CREATE TABLE IF NOT EXISTS conductors (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    rating DECIMAL(3,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Routes
CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    route_code VARCHAR(50) UNIQUE,
    name VARCHAR(200) NOT NULL,
    start_stop_id INT,
    end_stop_id INT,
    distance_km DECIMAL(10,2),
    estimated_duration_min INT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stops
CREATE TABLE IF NOT EXISTS stops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50),
    lat DECIMAL(10,6),
    lng DECIMAL(10,6),
    sequence_order INT,
    route_id INT REFERENCES routes(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Duty roster (crew assignment per bus per day)
CREATE TABLE IF NOT EXISTS duty_roster (
    id SERIAL PRIMARY KEY,
    bus_id INT NOT NULL REFERENCES buses(id),
    driver_id INT NOT NULL REFERENCES drivers(id),
    conductor_id INT NOT NULL REFERENCES conductors(id),
    route_id INT REFERENCES routes(id),
    duty_date DATE NOT NULL,
    shift_start TIME,
    shift_end TIME,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bus_id, duty_date)
);

-- Tickets (ACID for ticketing)
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50) UNIQUE NOT NULL,
    route_id INT REFERENCES routes(id),
    from_stop_id INT,
    to_stop_id INT,
    from_stop_name VARCHAR(200) NOT NULL,
    to_stop_name VARCHAR(200) NOT NULL,
    bus_id INT REFERENCES buses(id),
    passenger_name VARCHAR(200) NOT NULL,
    passenger_phone VARCHAR(20),
    passenger_email VARCHAR(255),
    travel_date DATE NOT NULL,
    travel_time VARCHAR(20),
    seats INT NOT NULL DEFAULT 1,
    fare_per_seat DECIMAL(10,2) NOT NULL,
    total_fare DECIMAL(10,2) NOT NULL,
    distance_km DECIMAL(10,2),
    seat_numbers TEXT,
    status VARCHAR(20) DEFAULT 'confirmed',
    qr_data TEXT,
    booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticket_id)
);

-- Passenger logs (for OD analytics and AI)
CREATE TABLE IF NOT EXISTS passenger_logs (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(50),
    from_stop_name VARCHAR(200),
    to_stop_name VARCHAR(200),
    passenger_count INT NOT NULL,
    travel_date DATE,
    travel_time VARCHAR(20),
    route_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Revenue logs
CREATE TABLE IF NOT EXISTS revenue_logs (
    id SERIAL PRIMARY KEY,
    route_id INT,
    ticket_id VARCHAR(50),
    amount DECIMAL(12,2) NOT NULL,
    log_date DATE,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cost logs
CREATE TABLE IF NOT EXISTS cost_logs (
    id SERIAL PRIMARY KEY,
    route_id INT,
    bus_id INT,
    cost_type VARCHAR(50),
    amount DECIMAL(12,2) NOT NULL,
    log_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Complaints (anonymous; admin only visibility)
CREATE TABLE IF NOT EXISTS complaints (
    id SERIAL PRIMARY KEY,
    complaint_id VARCHAR(50) UNIQUE NOT NULL,
    bus_number VARCHAR(20) NOT NULL,
    person_type VARCHAR(20) NOT NULL,
    person_id VARCHAR(20) NOT NULL,
    person_name VARCHAR(200),
    category VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI recommendations (stored for audit and linking)
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id SERIAL PRIMARY KEY,
    recommendation_type VARCHAR(50) NOT NULL,
    route_ref VARCHAR(200),
    priority VARCHAR(20),
    reason TEXT,
    confidence DECIMAL(3,2),
    expected_profit_impact DECIMAL(12,2),
    passenger_impact VARCHAR(100),
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Route merge suggestions
CREATE TABLE IF NOT EXISTS route_merge_suggestions (
    id SERIAL PRIMARY KEY,
    route_1_id INT,
    route_2_id INT,
    merged_route_path TEXT,
    new_timetable TEXT,
    projected_passengers INT,
    revenue_gain DECIMAL(12,2),
    loss_reduction DECIMAL(12,2),
    occupancy_1 DECIMAL(5,2),
    occupancy_2 DECIMAL(5,2),
    time_gap_min INT,
    status VARCHAR(20) DEFAULT 'proposed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tickets_travel_date ON tickets(travel_date);
CREATE INDEX IF NOT EXISTS idx_tickets_ticket_id ON tickets(ticket_id);
CREATE INDEX IF NOT EXISTS idx_passenger_logs_date ON passenger_logs(travel_date);
CREATE INDEX IF NOT EXISTS idx_complaints_bus ON complaints(bus_number);
CREATE INDEX IF NOT EXISTS idx_complaints_person ON complaints(person_id);
CREATE INDEX IF NOT EXISTS idx_duty_roster_date ON duty_roster(duty_date);
CREATE INDEX IF NOT EXISTS idx_duty_roster_bus ON duty_roster(bus_id);
