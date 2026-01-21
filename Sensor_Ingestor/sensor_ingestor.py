import os
import json
import time
import queue
import signal
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, List

import orjson
import paho.mqtt.client as mqtt
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import execute_values, Json
import re

# Environment
MQTT_HOST = os.getenv("MQTT_HOST", "host.docker.internal")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPICS = os.getenv("MQTT_TOPICS", "Data,sensors/#").split(',')

DB_HOST = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "postgresql"))
DB_NAME = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "FL"))
DB_USER = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "program"))
DB_PASS = os.getenv("DB_PASS", os.getenv("POSTGRES_PASSWORD", "program"))
DB_MIN_CONN = int(os.getenv("DB_MIN_CONN", "1"))
DB_MAX_CONN = int(os.getenv("DB_MAX_CONN", "5"))

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
BATCH_FLUSH_SECS = float(os.getenv("BATCH_FLUSH_SECS", "1.0"))

# Globals
pool: Optional[SimpleConnectionPool] = None
q: "queue.Queue[Tuple[Dict[str, Any], Dict[str, Any]] ]" = queue.Queue(maxsize=10000)
stop_flag = False

BRACKET_RE = re.compile(r"\[(.*?)\]")


def log(msg: str):
    print(f"[INGESTOR] {msg}", flush=True)


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


def init_db_pool():
    global pool
    while True:
        try:
            pool = SimpleConnectionPool(
                DB_MIN_CONN,
                DB_MAX_CONN,
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
            )
            log("DB pool initialized")
            return
        except Exception as e:
            log(f"DB connect failed: {e}. Retry in 3s")
            time.sleep(3)


def upsert_devices(conn, rows: List[Tuple[str, Optional[str], Optional[str], Optional[str]]]):
    if not rows:
        return
    with conn.cursor() as cur:
        execute_values(
            cur,
            (
                "INSERT INTO devices (device_id, name, type, location) VALUES %s "
                "ON CONFLICT (device_id) DO UPDATE SET "
                "name = COALESCE(EXCLUDED.name, devices.name), "
                "type = COALESCE(EXCLUDED.type, devices.type), "
                "location = COALESCE(EXCLUDED.location, devices.location)"
            ),
            rows,
        )


def insert_measurements(conn, rows: List[Tuple]):
    if not rows:
        return
    with conn.cursor() as cur:
        execute_values(
            cur,
            (
                "INSERT INTO measurements (ts, received_at, device_id, sensor, value, unit, place, msg_id, meta) "
                "VALUES %s ON CONFLICT DO NOTHING"
            ),
            rows,
        )


def parse_bracket_payload(raw: str) -> Optional[Dict[str, Any]]:
    try:
        parts = BRACKET_RE.findall(raw)
        if len(parts) < 4:
            return None
        device = parts[0]
        instruction = parts[2]
        if instruction != "Sending Data":
            return None
        details = parts[3]
        fields = {}
        for kv in details.split("|"):
            if ":" in kv:
                k, v = kv.split(":", 1)
                fields[k.strip()] = v.strip()
        sensor = fields.get("sensor")
        value = fields.get("value")
        if sensor is None or value is None:
            return None
        # optional
        place = fields.get("place")
        person = fields.get("person")
        path = fields.get("path")
        unit = fields.get("unit")
        msg_id = fields.get("msg_id")
        ts_raw = fields.get("ts")
        # compute ts
        if ts_raw:
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)
        # value cast
        try:
            val = float(value)
        except Exception:
            val = None
        meta = {"raw_details": details, "person": person, "path": path}
        return {
            "device_id": device,
            "sensor": sensor,
            "value": val,
            "unit": unit,
            "place": place,
            "msg_id": msg_id,
            "ts": ts,
            "meta": meta,
            "name": None,
            "type": None,
            "location": place,
        }
    except Exception:
        return None


def parse_json_payload(raw: str) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(raw)
        # accept either {instruction: "Sending Data", ...} or {type:"sensor", ...}
        instr = data.get("instruction")
        if instr and instr != "Sending Data":
            return None
        if not instr and data.get("type") not in ("sensor", "measurement"):
            return None
        device = data.get("device") or data.get("device_id")
        sensor = data.get("sensor")
        value = data.get("value")
        if not device or sensor is None or value is None:
            return None
        unit = data.get("unit")
        place = data.get("place")
        msg_id = data.get("msg_id")
        ts_raw = data.get("ts")
        if ts_raw:
            try:
                ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)
        try:
            val = float(value)
        except Exception:
            val = None
        meta = {k: v for k, v in data.items() if k not in {"device","device_id","sensor","value","unit","place","msg_id","ts","instruction","type"}}
        return {
            "device_id": device,
            "sensor": sensor,
            "value": val,
            "unit": unit,
            "place": place,
            "msg_id": msg_id,
            "ts": ts,
            "meta": meta,
            "name": data.get("device_name"),
            "type": data.get("device_type"),
            "location": place,
        }
    except Exception:
        return None


def compute_msg_id_fallback(d: Dict[str, Any], raw: str) -> str:
    base = f"{d.get('device_id')}|{d.get('sensor')}|{d.get('value')}|{d.get('unit')}|{d.get('place')}|{d.get('ts')}|{raw}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:64]


def worker_loop():
    global pool
    buf: List[Tuple] = []
    devices_buf: List[Tuple[str, Optional[str], Optional[str], Optional[str]]] = []
    last_flush = time.time()

    while not stop_flag:
        try:
            item = q.get(timeout=0.2)
        except queue.Empty:
            item = None

        now = time.time()
        if item is not None:
            parsed, _info = item
            devices_buf.append((parsed["device_id"], parsed.get("name"), parsed.get("type"), parsed.get("location")))
            buf.append((
                parsed["ts"],
                datetime.now(timezone.utc),
                parsed["device_id"],
                parsed["sensor"],
                parsed["value"],
                parsed.get("unit"),
                parsed.get("place"),
                parsed.get("msg_id"),
                Json(parsed.get("meta"))
            ))
        should_flush = len(buf) >= BATCH_SIZE or (buf and (now - last_flush) >= BATCH_FLUSH_SECS)
        if should_flush:
            try:
                if pool is None:
                    init_db_pool()
                assert pool is not None
                conn = pool.getconn()
                try:
                    # Deduplicate devices_buf: keep only latest record per device_id
                    devices_dedup = {}
                    for dev_id, name, type_, location in devices_buf:
                        devices_dedup[dev_id] = (dev_id, name, type_, location)
                    devices_dedup_list = list(devices_dedup.values())
                    
                    upsert_devices(conn, devices_dedup_list)
                    insert_measurements(conn, buf)
                    conn.commit()
                finally:
                    pool.putconn(conn)
                devices_buf.clear()
                buf.clear()
                last_flush = now
            except Exception as e:
                log(f"DB batch failed: {e}. Will retry after reconnect.")
                time.sleep(1)
                init_db_pool()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log("Connected to MQTT")
        for t in MQTT_TOPICS:
            t = t.strip()
            if t:
                client.subscribe(t)
                log(f"Subscribed {t}")
    else:
        log(f"MQTT connect failed rc={rc}")


def on_message(client, userdata, msg):
    raw = msg.payload.decode("utf-8", errors="ignore")
    parsed = None
    if raw.startswith("[") and raw.endswith("]"):
        parsed = parse_bracket_payload(raw)
    if parsed is None:
        parsed = parse_json_payload(raw)
    if parsed is None:
        return
    # Dedup fallback
    if not parsed.get("msg_id"):
        parsed["msg_id"] = compute_msg_id_fallback(parsed, raw)
    try:
        q.put_nowait((parsed, {"topic": msg.topic}))
    except queue.Full:
        log("Queue full, dropping measurement")


def shutdown(signum=None, frame=None):
    global stop_flag
    stop_flag = True


def main():
    init_db_pool()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect with retry; if fails, exit cleanly
    if not mqtt_connect_with_retry(client, MQTT_HOST, MQTT_PORT):
        log("Could not connect to MQTT after retries. Exiting.")
        return

    worker = None
    import threading
    worker = threading.Thread(target=worker_loop, daemon=True)
    worker.start()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        client.loop_start()
        while not stop_flag:
            time.sleep(0.5)
    finally:
        client.loop_stop()
        log("Exiting")


if __name__ == "__main__":
    main()
