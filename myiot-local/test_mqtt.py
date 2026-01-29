#!/usr/bin/env python3
import os
import sys

# Add paho-mqtt install
os.system('pip install -q paho-mqtt 2>/dev/null')

import paho.mqtt.client as mqtt
import json
import time

client = mqtt.Client(client_id='test_publisher')
client.connect('mosquitto', 1883)

messages = [
    ('myiot_local/salle_a_manger/sensor/light', {'value': 150, 'unit': 'lux', 'msg_id': 't1'}),
    ('myiot_local/bureau/sensor/light', {'value': 400, 'unit': 'lux', 'msg_id': 't2'}),
    ('myiot_local/chambre/sensor/temperature', {'value': 22.5, 'unit': 'C', 'msg_id': 'b1'}),
    ('myiot_local/salon/sensor/light', {'value': 200, 'unit': 'lux', 'msg_id': 'dup1'}),
    ('myiot_local/salon/sensor/light', {'value': 200, 'unit': 'lux', 'msg_id': 'dup1'}),
]

print('Testing MyIoT Stack...\n')
for i, (topic, payload) in enumerate(messages):
    msg = json.dumps(payload)
    client.publish(topic, msg)
    print(f'✓ Test {i+1}: Published to {topic}')
    print(f'  Payload: {msg}')
    time.sleep(0.3)

client.disconnect()
print('\n✅ All tests published successfully!')
