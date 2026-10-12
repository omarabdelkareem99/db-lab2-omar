-- OPTIONAL EXTRA (not part of the lab requirements).
-- Only needed for the "Forgot password" feature. Run after schema.sql:
--   mysql -u root -p registration < database/extras_password_reset.sql
USE registration;

CREATE TABLE IF NOT EXISTS verification_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    code_hash CHAR(64) NOT NULL,
    purpose VARCHAR(30) NOT NULL DEFAULT 'reset_password',
    expires_at DATETIME NOT NULL,
    attempts INT NOT NULL DEFAULT 0,
    used TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);
