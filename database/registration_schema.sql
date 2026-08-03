-- Registration logs for audit trail\r
CREATE TABLE IF NOT EXISTS registration_logs (\r
    id SERIAL PRIMARY KEY,\r
    user_id INT REFERENCES users(id),\r
    action VARCHAR(50) NOT NULL,\r
    performed_by INT REFERENCES users(id),\r
    details TEXT,\r
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\r
);\r
\r
-- Index for registration status queries\r
CREATE INDEX IF NOT EXISTS idx_users_approval_status ON users(approval_status);\r
CREATE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id);\r
