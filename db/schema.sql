-- Schema unificado FarmTech (PostgreSQL)

CREATE TABLE IF NOT EXISTS sensors (
    id SERIAL PRIMARY KEY,
    sensor_id TEXT,
    umidade REAL,
    nutriente REAL,
    ts TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP,
    temp REAL,
    chuva REAL,
    vento REAL
);

CREATE TABLE IF NOT EXISTS detections (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP,
    categoria TEXT,
    confianca REAL,
    meta JSONB
);

CREATE INDEX IF NOT EXISTS idx_sensors_ts ON sensors(ts);
CREATE INDEX IF NOT EXISTS idx_weather_ts ON weather(ts);
CREATE INDEX IF NOT EXISTS idx_detections_ts ON detections(ts);
