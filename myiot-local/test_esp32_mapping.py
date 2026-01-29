"""
Simple MQTT integration test for esp32_multi_debug mappings.

What it does:
- Subscribes to sensor topics for channel 1 and 2.
- Publishes actuator ON/OFF commands to the mapped actuator rooms.
- Waits for sensor messages (periodic publishes from firmware) and reports results.

Usage:
  python test_esp32_mapping.py --host localhost --port 1884

Requires: paho-mqtt
"""
import argparse
import time
import threading
import json
from collections import defaultdict

import paho.mqtt.client as mqtt

SENSOR_TOPICS = [
    "myiot_local/salle_a_manger/sensor/button1",
    "myiot_local/cuisine/sensor/button2",
]

ACTUATOR_TOPICS = [
    "myiot_local/salle_a_manger/actuator/lamp1/cmd",
    "myiot_local/salle_a_manger/actuator/lamp2/cmd",
]


class TestRunner:
    def __init__(self, host, port, timeout=10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client = mqtt.Client("test_harness")
        self.received = defaultdict(list)
        self.lock = threading.Lock()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to broker rc=", rc)
        for t in SENSOR_TOPICS:
            client.subscribe(t)
            print("Subscribed to", t)

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
        except Exception:
            payload = str(msg.payload)
        with self.lock:
            self.received[msg.topic].append(payload)
        print(f"RECV {msg.topic} => {payload}")

    def run(self):
        self.client.connect(self.host, self.port, 60)
        self.client.loop_start()

        # Give firmware time to publish periodic sensor messages
        print(f"Waiting {self.timeout}s for sensor messages...")
        time.sleep(self.timeout)

        # Publish actuator commands: ON then OFF
        for t in ACTUATOR_TOPICS:
            msg = json.dumps({"state": "ON"})
            print("Publishing", t, msg)
            self.client.publish(t, msg)
            time.sleep(0.5)
        time.sleep(1)
        for t in ACTUATOR_TOPICS:
            msg = json.dumps({"state": "OFF"})
            print("Publishing", t, msg)
            self.client.publish(t, msg)
            time.sleep(0.2)

        # Wait a bit for any final sensor publishes
        time.sleep(2)
        self.client.loop_stop()
        self.client.disconnect()

    def report(self):
        print("\nTest report:")
        ok = True
        for t in SENSOR_TOPICS:
            msgs = self.received.get(t, [])
            print(f"  {t}: {len(msgs)} messages")
            if len(msgs) == 0:
                ok = False
        return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='localhost')
    ap.add_argument('--port', type=int, default=1884)
    ap.add_argument('--timeout', type=int, default=8)
    args = ap.parse_args()

    tr = TestRunner(args.host, args.port, timeout=args.timeout)
    tr.run()
    success = tr.report()
    if success:
        print("\nRESULT: SUCCESS — sensor messages received for all expected topics.")
        raise SystemExit(0)
    else:
        print("\nRESULT: FAILURE — missing sensor messages for some topics.")
        raise SystemExit(2)


if __name__ == '__main__':
    main()
