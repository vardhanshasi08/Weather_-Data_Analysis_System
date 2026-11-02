-- Run this script in the Neon SQL Editor before using the hosted app.
CREATE TABLE IF NOT EXISTS weather_records (
    record_id BIGSERIAL PRIMARY KEY,
    observation_date DATE NOT NULL,
    location VARCHAR(120) NOT NULL,
    temperature NUMERIC(5,2) NOT NULL,
    humidity NUMERIC(5,2) NOT NULL,
    rainfall NUMERIC(7,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_humidity CHECK (humidity >= 0 AND humidity <= 100),
    CONSTRAINT chk_temperature CHECK (temperature >= -90 AND temperature <= 65),
    CONSTRAINT chk_rainfall CHECK (rainfall >= 0),
    CONSTRAINT uq_weather_date_location UNIQUE (observation_date, location)
);
CREATE INDEX IF NOT EXISTS idx_observation_date ON weather_records (observation_date);
