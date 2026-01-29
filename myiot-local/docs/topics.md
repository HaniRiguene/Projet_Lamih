# Topics conventions (per-room format)

This document describes the MQTT topic conventions used in the MyIoT local stack after migration to a per-room layout.

## New canonical format

- Prefix: `myiot_local`
- Sensor topics: `myiot_local/<room>/sensor/<sensor_type>`
- Actuator commands: `myiot_local/<room>/actuator/<actuator_id>/cmd`

Examples:
```
myiot_local/salon/sensor/light
myiot_local/salon/sensor/temperature
myiot_local/chambre/sensor/light
myiot_local/salle_a_manger/sensor/light
```

## Wildcards

- Subscribe to all sensors: `myiot_local/+/sensor/+` (recommended for services)
- All topics under a room: `myiot_local/<room>/#`

## Publishing payload format

Sensors publish JSON payloads like:

```json
{"value": 123, "unit": "lux", "msg_id": "unique-id"}
```

Actuators accept payloads like:

```json
{"state": "ON"}
```

## Migration notes

1. Update ESP32 firmware to publish sensor topics using the `myiot_local/<room>/sensor/...` pattern.
2. Update services to subscribe to `myiot_local/+/sensor/+` (already applied to `ingestor.py` and `automation.py`).
3. Replace actuator commands with `myiot_local/<room>/actuator/<actuator_id>/cmd`.

## Examples for your setup

Rooms: `salle_a_manger`, `salon`, `salle_de_bain`, `cuisine`
Sensors per room: `light`, `temperature`, `button`, `motion`

Publish examples:
```
myiot_local/salon/sensor/light -> {"value": 150, "unit":"lux", "msg_id":"..."}
myiot_local/salon/sensor/button -> {"value": 1, "unit":"binary", "msg_id":"..."}
myiot_local/salon/sensor/motion -> {"value": 1, "unit":"binary", "msg_id":"..."}
```

Actuator command example to turn lamp on in salon:
```
myiot_local/salon/actuator/lamp1/cmd -> {"state":"ON"}
```
