import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Optional

import paho.mqtt.client as mqtt

# Env configuration
MQTT_HOST = os.getenv("MQTT_HOST", "host.docker.internal")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# Light control configuration
SENSOR_TOPIC = os.getenv("SENSOR_TOPIC", "Data")  # subscribes to raw sensor messages
SENSOR_NAME = os.getenv("LIGHT_SENSOR_NAME", "light")
LAMP_ID = os.getenv("LAMP_ID", "lamp1")
ACTUATOR_TOPIC = os.getenv("ACTUATOR_TOPIC", f"actuators/{LAMP_ID}/set")

TH_LOW = float(os.getenv("TH_LOW", "200.0"))
TH_HIGH = float(os.getenv("TH_HIGH", "300.0"))
DUR_ON = float(os.getenv("DUR_ON_SECS", "5.0"))      # below low for N seconds
DUR_OFF = float(os.getenv("DUR_OFF_SECS", "5.0"))     # above high for M seconds

STATE_OFF = "OFF"
STATE_ON = "ON"

# Internal state
current_state = STATE_OFF
below_since: Optional[float] = None
above_since: Optional[float] = None


def log(msg: str):
    print(f"[AUTOMATION] {msg}", flush=True)


def mqtt_connect_with_retry(client, host: str, port: int, max_retries: int = 30, backoff_start: float = 0.5):
    """
    Connect to MQTT broker with exponential backoff retry.
    Logs each attempt; does not crash on failure.
    """
    retries = 0
    backoff = backoff_start
    while retries < max_retries:
        try:
            client.connect(host, port, keepalive=60)
            log(f"Connected to MQTT at {host}:{port}")
            return True
        except Exception as e:
            retries += 1
            log(f"MQTT connect attempt {retries}/{max_retries} failed: {e}. Retry in {backoff:.1f}s...")
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 30.0)
    log(f"Failed to connect to MQTT after {max_retries} attempts.")
    return False


def parse_bracket(raw: str):
    # format: [device][0][Sending Data][sensor:...|value:...|place:...]  (we only care sensor/value)
    import re
    parts = re.findall(r"\[(.*?)\]", raw)
    if len(parts) < 4:
        return None
    if parts[2] != "Sending Data":
        return None
    det = parts[3]
    fields = {}
    for kv in det.split("|"):
        if ":" in kv:
            k, v = kv.split(":", 1)
            fields[k.strip()] = v.strip()
    sensor = fields.get("sensor")
    value = fields.get("value")
    if sensor is None or value is None:
        return None
    try:
        v = float(value)
    except Exception:
        return None
    return {"sensor": sensor, "value": v}


def parse_json(raw: str):
    try:
        data = json.loads(raw)
        sensor = data.get("sensor")
        value = data.get("value")
        if sensor is None or value is None:
            return None
        try:
            v = float(value)
        except Exception:
            return None
        return {"sensor": sensor, "value": v}
    except Exception:
        return None


def publish_state(client: mqtt.Client, state: str):
    payload = json.dumps({"state": state})
    client.publish(ACTUATOR_TOPIC, payload)
    log(f"Publish {payload} to {ACTUATOR_TOPIC}")


def process_value(client: mqtt.Client, sensor: str, value: float):
    global current_state, below_since, above_since
    now = time.time()

    if sensor != SENSOR_NAME:
        return

    if current_state == STATE_OFF:
        # consider turning ON if below low
        if value < TH_LOW:
            if below_since is None:
                below_since = now
            if now - below_since >= DUR_ON:
                current_state = STATE_ON
                below_since = None
                above_since = None
                publish_state(client, STATE_ON)
        else:
            below_since = None
    else:
        # current_state == ON -> consider turning OFF if above high
        if value > TH_HIGH:
            if above_since is None:
                above_since = now
            if now - above_since >= DUR_OFF:
                current_state = STATE_OFF
                below_since = None
                above_since = None
                publish_state(client, STATE_OFF)
        else:
            above_since = None


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log("Connected to MQTT")
        client.subscribe(SENSOR_TOPIC)
        log(f"Subscribed {SENSOR_TOPIC}")
    else:
        log(f"MQTT connect failed rc={rc}")


def on_message(client, userdata, msg):
    raw = msg.payload.decode("utf-8", errors="ignore")
    parsed = None
    if raw.startswith("[") and raw.endswith("]"):
        parsed = parse_bracket(raw)
    if parsed is None:
        parsed = parse_json(raw)
    if parsed is None:
        return
    process_value(client, parsed["sensor"], parsed["value"])


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect with retry; if fails, exit cleanly
    if not mqtt_connect_with_retry(client, MQTT_HOST, MQTT_PORT):
        log("Could not connect to MQTT after retries. Exiting.")
        return

    client.loop_forever()


if __name__ == "__main__":
    main()
