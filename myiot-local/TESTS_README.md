Running ESP32 MQTT mapping tests

Prerequisites
- Broker reachable at `localhost:1884` (use docker exec if using container port mapping to 1883)
- Python 3.8+ and `pip install -r requirements-tests.txt`

Quick start

1) Install test deps:

```bash
pip install -r requirements-tests.txt
```

2) Run the test script (it will subscribe to sensor topics and publish actuator cmds):

```bash
python test_esp32_mapping.py --host localhost --port 1884 --timeout 8
```

Interpreting results
- Exit code 0: success (sensor messages observed for both topics)
- Exit code 2: failure (missing sensor messages)

Notes
- The tests expect the ESP32 firmware to periodically publish sensor states (every 5s by default).
- If the ESP is not connected, tests will report failure; you can increase `--timeout` to wait longer for the first publish.
