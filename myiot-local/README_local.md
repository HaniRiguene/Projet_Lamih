# MyIoT Local Stack - Tests & Instructions

## Structure

```
myiot-local/
├── docker-compose.local.yml    # Orchestration (Mosquitto + Postgres)
├── schema.sql                   # Database schema
├── ingestor.py                  # MQTT → Postgres ingestion
├── automation.py                # Light automation rules
├── Dockerfile.ingestor
├── Dockerfile.automation
├── requirements-ingestor.txt
├── requirements-automation.txt
├── mosquitto.conf              # MQTT broker config
└── README_local.md             # This file
```

## Stack Components

### Ports (Isolated from StageFL)
- **Mosquitto**: `1884:1883` (MQTT broker)
- **Postgres**: `5434:5432` (Database)

### MQTT Namespace
```
myiot_local/<room>/sensor/<sensor_type>         # Sensor data (ingestor, automation)
myiot_local/<room>/actuator/<actuator_id>/cmd   # Actuator commands (automation → broker)
```

### Sensor Payload Format
```json
{
  "value": 150,
  "unit": "lux",
  "msg_id": "t1"
}
```

### Actuator Payload Format
```json
{
  "state": "ON"
}
```

## Database Schema

### Tables
- **devices**: `(device_id, device_type, location, created_at)`
- **measurements**: `(id, device_id, sensor_type, value, unit, msg_id, received_at)`
  - Constraint: `UNIQUE(device_id, msg_id)` → prevents duplicates
- **actuators**: `(actuator_id, actuator_type, location, created_at)`
- **actuator_states**: `(id, actuator_id, state, triggered_by, updated_at)`

## Components Description

### Ingestor (`ingestor.py`)
- **Role**: MQTT → Postgres data pipeline
- **Behavior**:
  - Subscribes to `myiot_local/+/sensor/+`
  - Parses topic: `myiot_local/<room>/sensor/<sensor_type>`
  - Extracts `room` (used as `device_id`), `sensor_type` from topic
  - Inserts into `measurements` table
  - Auto-creates device in `devices` table if missing
  - Handles duplicates gracefully (unique constraint on `device_id, msg_id`)

### Automation (`automation.py`)
- **Role**: Event-driven automation engine
- **Behavior**:
  - Subscribes to `myiot_local/+/sensor/+`
  - **Light Rule**:
    - Value < 200 lux → publishes `{"state":"ON"}` to `myiot_local/<room>/actuator/lamp1/cmd`
    - Value > 300 lux → publishes `{"state":"OFF"}` to `myiot_local/<room>/actuator/lamp1/cmd`
    - Range 200-300 lux → no action (hysteresis)

## Quick Start

### 1. Start the Stack
```bash
cd myiot-local
docker compose -f docker-compose.local.yml up -d
```

Verify all services are running:
```bash
docker compose -f docker-compose.local.yml ps
```

Expected output:
```
NAME                COMMAND                  SERVICE        STATUS
myiot_mosquitto     /docker-entrypoint.sh    mosquitto      Up
myiot_postgres      /docker-entrypoint.sh    postgres       Up
myiot_ingestor      python ingestor.py       ingestor       Up
myiot_automation    python automation.py     automation     Up
```

### 2. Check Logs
```bash
# View all logs
docker compose -f docker-compose.local.yml logs -f

# View specific service
docker compose -f docker-compose.local.yml logs -f ingestor
docker compose -f docker-compose.local.yml logs -f automation
```

## Test Scenarios

### Test 1: Basic Sensor Ingestion
**Objective**: Verify ingestor reads sensor data and stores in DB

**Steps**:
```bash
# Terminal 1: Monitor database
docker exec -it myiot_postgres psql -U myiot_user -d myiot_db -c \
  "SELECT device_id, sensor_type, value, unit, msg_id, received_at FROM measurements ORDER BY received_at DESC LIMIT 10;"

# Terminal 2: Publish a light sensor reading (low light)
docker exec -it myiot_mosquitto mosquitto_pub \
  -h localhost -p 1883 \
  -t myiot_local/salle_a_manger/sensor/light \
  -m '{"value":150,"unit":"lux","msg_id":"t1"}'

# Terminal 3: Listen to actuator commands
docker exec -it myiot_mosquitto mosquitto_sub \
  -h localhost -p 1883 \
  -t 'myiot_local/+/actuator/#' \
  -v
```

**Expected Results**:
- Ingestor logs: `Inserted measurement: device=salle_a_manger, sensor=light, value=150`
- Automation logs: `Automation triggered: Light < 200 (value=150) -> Lamp ON`
- Actuator topic receives: `myiot_local/<room>/actuator/lamp1/cmd {"state":"ON"}`
- DB query shows new row with `salle_a_manger | light | 150 | lux | t1`

### Test 2: Automation - Light Threshold
**Objective**: Verify automation rules trigger correctly

**Scenario A: Low light (< 200 lux)**
```bash
docker exec -it myiot_mosquitto mosquitto_pub \
  -h localhost -p 1883 \
  -t myiot_local/bureau/sensor/light \
  -m '{"value":100,"unit":"lux","msg_id":"t2"}'
```
Expected: Lamp ON published

**Scenario B: High light (> 300 lux)**
```bash
docker exec -it myiot_mosquitto mosquitto_pub \
  -h localhost -p 1883 \
  -t myiot_local/bureau/sensor/light \
  -m '{"value":400,"unit":"lux","msg_id":"t3"}'
```
Expected: Lamp OFF published

**Scenario C: Neutral zone (200-300 lux)**
```bash
docker exec -it myiot_mosquitto mosquitto_pub \
  -h localhost -p 1883 \
  -t myiot_local/bureau/sensor/light \
  -m '{"value":250,"unit":"lux","msg_id":"t4"}'
```
Expected: No action (no publish)

### Test 3: Duplicate Prevention
**Objective**: Verify unique constraint on `(device_id, msg_id)`

```bash
# Publish same message twice
docker exec -it myiot_mosquitto mosquitto_pub \
  -h localhost -p 1883 \
  -t myiot_local/salon/sensor/light \
  -m '{"value":180,"unit":"lux","msg_id":"dup1"}'

docker exec -it myiot_mosquitto mosquitto_pub \
  -h localhost -p 1883 \
  -t myiot_local/salon/sensor/light \
  -m '{"value":180,"unit":"lux","msg_id":"dup1"}'

# Check DB
docker exec -it myiot_postgres psql -U myiot_user -d myiot_db -c \
  "SELECT COUNT(*) FROM measurements WHERE device_id='salon' AND msg_id='dup1';"
```

Expected: Count = 1 (duplicate ignored)

### Test 4: Multiple Sensors
**Objective**: Test multi-device ingestion

```bash
# Device 1 - Kitchen light
docker exec -it myiot_mosquitto mosquitto_pub \
  -h localhost -p 1883 \
  -t myiot_local/cuisine/sensor/light \
  -m '{"value":250,"unit":"lux","msg_id":"k1"}'

# Device 2 - Bedroom temperature
docker exec -it myiot_mosquitto mosquitto_pub \
  -h localhost -p 1883 \
  -t myiot_local/chambre/sensor/temperature \
  -m '{"value":22.5,"unit":"°C","msg_id":"b1"}'

# Device 3 - Living room humidity
docker exec -it myiot_mosquitto mosquitto_pub \
  -h localhost -p 1883 \
  -t myiot_local/salon/sensor/humidity \
  -m '{"value":55,"unit":"%","msg_id":"l1"}'

# Verify all inserted
docker exec -it myiot_postgres psql -U myiot_user -d myiot_db -c \
  "SELECT device_id, sensor_type, value, unit FROM measurements ORDER BY received_at DESC LIMIT 10;"
```

### Test 5: Database Query Examples
```bash
# Connect to DB
docker exec -it myiot_postgres psql -U myiot_user -d myiot_db

# Once inside psql:

-- All measurements
SELECT * FROM measurements ORDER BY received_at DESC;

-- Latest 20 measurements
SELECT device_id, sensor_type, value, unit, msg_id, received_at 
FROM measurements 
ORDER BY received_at DESC 
LIMIT 20;

-- Measurements by device
SELECT * FROM measurements WHERE device_id = 'salle_a_manger' ORDER BY received_at DESC;

-- Count by sensor type
SELECT sensor_type, COUNT(*) as count FROM measurements GROUP BY sensor_type;

-- All devices
SELECT * FROM devices;

-- Actuator states
SELECT * FROM actuator_states ORDER BY updated_at DESC;

-- Exit
\q
```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker compose -f docker-compose.local.yml logs

# Restart all
docker compose -f docker-compose.local.yml restart

# Full reset (WARNING: deletes database data)
docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up -d
```

### Can't connect to Mosquitto
```bash
# Verify broker is running
docker exec myiot_mosquitto mosquitto_sub -h localhost -p 1883 -t '$SYS/#' -W 1
```

### Can't connect to Postgres
```bash
# Verify connectivity
docker exec myiot_postgres pg_isready -U myiot_user
```

### Ingestor/Automation not receiving messages
- Check logs: `docker compose -f docker-compose.local.yml logs ingestor`
- Verify topic format: `myiot_local/<room>/sensor/<sensor_type>`
- Verify payload has `value` field

## Stop & Cleanup

```bash
# Stop services (keeps data)
docker compose -f docker-compose.local.yml down

# Full cleanup (deletes everything)
docker compose -f docker-compose.local.yml down -v
```

## Notes

- All containers use isolated network `myiot_network`
- Database persists in Docker volume `myiot_postgres_data`
- Ingestor & Automation have built-in retry logic for DB connections
- Automation uses state tracking to prevent duplicate commands
- Message IDs (`msg_id`) prevent re-processing of duplicate MQTT publishes
