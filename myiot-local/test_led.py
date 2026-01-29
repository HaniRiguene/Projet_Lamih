#!/usr/bin/env python3
"""
Test script pour allumer/éteindre la LED de l'ESP32
via le broker MQTT
"""
import os
import sys

# Install paho-mqtt if needed
os.system('pip install -q paho-mqtt 2>/dev/null')

import paho.mqtt.client as mqtt
import json
import time
import sys

HOST = 'localhost'
PORT = 1884
# Example: publish to the salon lamp actuator command topic
TOPIC = 'myiot_local/salon/actuator/lamp1/cmd'

def test_led():
    print("=== ESP32 LED Test ===\n")
    
    client = mqtt.Client(client_id='test_led')
    
    try:
        print(f"Connecting to MQTT {HOST}:{PORT}...")
        client.connect(HOST, PORT, keepalive=60)
        print("✓ Connected\n")
        
        # Test 1: Turn LED ON
        print("Test 1: Sending LED ON command...")
        msg = json.dumps({"state": "ON"})
        client.publish(TOPIC, msg)
        print(f"  Topic: {TOPIC}")
        print(f"  Payload: {msg}")
        print("  ✓ Check ESP32 Serial Monitor for: ✅ → LED ON\n")
        
        time.sleep(2)
        
        # Test 2: Turn LED OFF
        print("Test 2: Sending LED OFF command...")
        msg = json.dumps({"state": "OFF"})
        client.publish(TOPIC, msg)
        print(f"  Topic: {TOPIC}")
        print(f"  Payload: {msg}")
        print("  ✓ Check ESP32 Serial Monitor for: ✅ → LED OFF\n")
        
        time.sleep(2)
        
        # Test 3: Turn LED ON again (blink test)
        print("Test 3: Blink test (ON → OFF → ON)...")
        for i in range(3):
            state = "ON" if i % 2 == 0 else "OFF"
            msg = json.dumps({"state": state})
            client.publish(TOPIC, msg)
            print(f"  → LED {state}")
            time.sleep(0.5)
        
        print("\n✅ All tests sent! Check ESP32 Serial Monitor for responses.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.disconnect()

if __name__ == '__main__':
    test_led()
