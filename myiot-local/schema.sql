-- Schema for MyIoT local stack
-- Devices table
CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(255) PRIMARY KEY,
    device_type VARCHAR(50) NOT NULL,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Measurements table
CREATE TABLE IF NOT EXISTS measurements (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    value DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20),
    msg_id VARCHAR(255),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    UNIQUE(device_id, msg_id)
);

-- Actuators table
CREATE TABLE IF NOT EXISTS actuators (
    actuator_id VARCHAR(255) PRIMARY KEY,
    actuator_type VARCHAR(50) NOT NULL,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Actuator states table
CREATE TABLE IF NOT EXISTS actuator_states (
    id SERIAL PRIMARY KEY,
    actuator_id VARCHAR(255) NOT NULL,
    state VARCHAR(20) NOT NULL,
    triggered_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actuator_id) REFERENCES actuators(actuator_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_measurements_device_id ON measurements(device_id, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_measurements_sensor_type ON measurements(sensor_type, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_actuator_states_actuator_id ON actuator_states(actuator_id, updated_at DESC);
