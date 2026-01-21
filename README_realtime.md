# Realtime Sensor Ingestion & API

This adds a robust, PostgreSQL-backed time-series pipeline without breaking the existing FL orchestrator and logs.

## Architecture
- MQTT broker (existing).
- Orchestrator (existing) keeps CSV writes; a new `sensor_ingestor` consumes the same messages and writes to DB.
- PostgreSQL 14 (TimescaleDB optional):
  - `devices(device_id, name, type, location, created_at)`
  - `measurements(ts, received_at, device_id, sensor, value, unit, place, msg_id, meta jsonb)`
  - Unique: `(device_id, msg_id)` for dedupe when `msg_id` present.
  - If TimescaleDB is present, `measurements` becomes a hypertable on `ts`.
- FastAPI (`Serveur_API/server_api.py`): new mobile endpoints under `/v1/...`.
- Automation service (`automation`): simple hysteresis rule to control a lamp via MQTT.

## Environment Variables
- Ingestor
  - `MQTT_HOST` (default `host.docker.internal` in code, set to `172.18.0.1` in compose)
  - `MQTT_PORT` (default `1883`)
  - `DB_HOST` (`postgresql` in compose)
  - `DB_NAME` (`FL`)
  - `DB_USER` (`program`)
  - `DB_PASS` (`program`)
  - `BATCH_SIZE` (default `100`)
  - `BATCH_FLUSH_SECS` (default `1.0`)
- Automation
  - `SENSOR_TOPIC` (`Data`)
  - `LIGHT_SENSOR_NAME` (`light`)
  - `LAMP_ID` (`lamp1`)
  - `TH_LOW`/`TH_HIGH` (`200` / `300`)
  - `DUR_ON_SECS`/`DUR_OFF_SECS` (`5` / `5`)

## How to Run
Using the repository’s `docker-compose.yml`:

```bash
# From repository root
docker compose up -d --build
```

Services:
- `PostgreSQL` on host port `5433`.
- `Server_API` on host port `8000`.
- `Sensor_Ingestor` and `Automation_Service` run in background.

## Testing

### Publish test sensor data (MQTT)
Current legacy format (CSV-compatible):
```bash
mosquitto_pub -h 127.0.0.1 -p 1883 -t Data -m "[device-123][0][Sending Data][sensor:light|value:180|place:room|unit:lux|msg_id:abc-1|ts:2026-01-20T10:00:00Z]"
```

JSON option:
```bash
mosquitto_pub -h 127.0.0.1 -p 1883 -t sensors/light -m '{"instruction":"Sending Data","device":"device-123","sensor":"light","value":320,"unit":"lux","place":"room","msg_id":"abc-2","ts":"2026-01-20T10:05:00Z"}'
```

### Query API
List devices:
```bash
curl http://localhost:8000/v1/devices
```

Latest per sensor for a device:
```bash
curl http://localhost:8000/v1/devices/device-123/latest
```

History (filters optional):
```bash
curl "http://localhost:8000/v1/measurements?device_id=device-123&sensor=light&from=2026-01-20T10:00:00Z&to=2026-01-20T12:00:00Z&limit=1000"
```

Aggregate (Timescale `time_bucket` if available, else SQL fallback):
```bash
curl "http://localhost:8000/v1/measurements/aggregate?device_id=device-123&sensor=light&bucket=5m&agg=avg&from=2026-01-20T10:00:00Z&to=2026-01-20T12:00:00Z"
```

### Automation
Send low-light values (< TH_LOW) for `DUR_ON_SECS` to trigger ON:
```bash
mosquitto_pub -h 127.0.0.1 -p 1883 -t Data -m "[device-123][0][Sending Data][sensor:light|value:150|place:room]"
```
After a few seconds above `TH_HIGH`, OFF will be published to `actuators/lamp1/set`.

## Notes
- Existing orchestrator (`Serveur_Client/server_main_program.py`) is unchanged; its CSV function `save_data_locally()` remains for backward compatibility. The new ingestor independently stores to DB.
- SQL is parameterized in API and ingestor uses connection pooling.
- Deduplication uses `(device_id, msg_id)` when provided; otherwise a SHA-256 fallback in the ingestor.
