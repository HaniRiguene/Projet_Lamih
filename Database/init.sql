-- ************************************************************
-- Partie 1 : Configuration de l'utilisateur et des privilèges
-- ************************************************************

-- Créer l'utilisateur 'program' s'il n'existe pas, avec le mot de passe 'program'
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'program') THEN
      CREATE USER program WITH PASSWORD 'program';
   END IF;
END
$$;

-- Accorder les droits à l'utilisateur 'program' sur la base de données "FL"
-- NOTE: L'utilisation des guillemets doubles ("FL") force la casse majuscule.
GRANT ALL PRIVILEGES ON DATABASE "FL" TO program;


-- ************************************************************
-- Partie 2 : Création des tables (dans la base "FL")
-- ************************************************************

-- Table hubs
CREATE TABLE hubs (
    hub_id SERIAL PRIMARY KEY,
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(30) NOT NULL,
    status VARCHAR(10) NOT NULL,
    stockage VARCHAR(10) DEFAULT '0'
);

-- Table models
CREATE TABLE models (
    Model_id SERIAL PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    Path VARCHAR(255) NOT NULL,
    Uploaded_by VARCHAR(30) NOT NULL,
    Upload_date DATE NOT NULL DEFAULT CURRENT_DATE,
    Description TEXT
);

-- Table datasets
CREATE TABLE datasets (
    dataset_id SERIAL PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    Path VARCHAR(255) NOT NULL,
    Uploaded_by VARCHAR(30) NOT NULL,
    Upload_date DATE NOT NULL DEFAULT CURRENT_DATE,
    Description TEXT
);

-- Table jobs
CREATE TABLE jobs ( 
    jobs_id SERIAL PRIMARY KEY, 
    Hubs TEXT[] NOT NULL, 
    Datasets TEXT[] NOT NULL, 
    Model_id INT NOT NULL REFERENCES models(model_id),
    Status VARCHAR(50),
    Start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    End_time TIMESTAMP 
);

-- Table logs
CREATE TABLE IF NOT EXISTS logs (
    log_id SERIAL PRIMARY KEY,
    hub_name VARCHAR(255) NOT NULL,  
    logs TEXT NOT NULL,               
    type VARCHAR(50) NOT NULL,        
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ************************************************************
-- Partie 3 : Données temps réel (devices, measurements)
-- ************************************************************

-- Activer TimescaleDB si disponible (sans échouer si non installé)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb'
    ) THEN
        CREATE EXTENSION IF NOT EXISTS timescaledb;
    END IF;
END
$$;

-- Table des devices (identifiés par un device_id libre)
CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(255),
    type VARCHAR(64),
    location VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table des mesures capteurs
CREATE TABLE IF NOT EXISTS measurements (
    ts TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id VARCHAR(128) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    sensor VARCHAR(128) NOT NULL,
    value DOUBLE PRECISION,
    unit VARCHAR(32),
    place VARCHAR(255),
    msg_id VARCHAR(128),
    meta JSONB,
    PRIMARY KEY (device_id, ts, sensor)
);

-- Index pour accélérer les requêtes courantes
CREATE INDEX IF NOT EXISTS idx_measurements_ts ON measurements (ts DESC);
CREATE INDEX IF NOT EXISTS idx_measurements_device_sensor_ts ON measurements (device_id, sensor, ts DESC);
CREATE INDEX IF NOT EXISTS idx_measurements_msgid ON measurements (device_id, msg_id);

-- Pas de contrainte UNIQUE sur msg_id car il peut être NULL
-- La déduplication se fera via la PRIMARY KEY (device_id, ts, sensor)

-- Créer une hypertable Timescale si l'extension est disponible
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
    ) THEN
        PERFORM public.create_hypertable('measurements', 'ts', if_not_exists => TRUE);
    END IF;
END
$$;

-- S'assurer que l'utilisateur program a accès aux nouvelles tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO program;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO program;