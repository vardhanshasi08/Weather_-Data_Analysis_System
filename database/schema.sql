CREATE DATABASE IF NOT EXISTS weather_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE weather_analysis;
CREATE TABLE IF NOT EXISTS weather_records (
    record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    observation_date DATE NOT NULL,
    location VARCHAR(120) NOT NULL,
    temperature DECIMAL(5,2) NOT NULL COMMENT 'Degrees Celsius',
    humidity DECIMAL(5,2) NOT NULL COMMENT 'Relative humidity percentage',
    rainfall DECIMAL(7,2) NOT NULL DEFAULT 0 COMMENT 'Rainfall in millimetres',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_humidity CHECK (humidity >= 0 AND humidity <= 100),
    CONSTRAINT chk_temperature CHECK (temperature >= -90 AND temperature <= 65),
    CONSTRAINT chk_rainfall CHECK (rainfall >= 0),
    INDEX idx_observation_date (observation_date),
    UNIQUE KEY uq_weather_date_location (observation_date, location)
);
