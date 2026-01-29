#!/bin/bash

# Test 1: Low light (< 200 lux)
echo "Test 1: Publishing low light (150 lux)..."
mosquitto_pub -h localhost -p 1883 -t myiot_local/salle_a_manger/sensor/light -m '{"value":150,"unit":"lux","msg_id":"t1"}'

sleep 1

# Test 2: High light (> 300 lux)
echo "Test 2: Publishing high light (400 lux)..."
mosquitto_pub -h localhost -p 1883 -t myiot_local/bureau/sensor/light -m '{"value":400,"unit":"lux","msg_id":"t2"}'

sleep 1

# Test 3: Temperature sensor
echo "Test 3: Publishing temperature (22.5°C)..."
mosquitto_pub -h localhost -p 1883 -t myiot_local/chambre/sensor/temperature -m '{"value":22.5,"unit":"°C","msg_id":"b1"}'

sleep 1

# Test 4: Duplicate prevention test
echo "Test 4: Publishing duplicate (same msg_id)..."
mosquitto_pub -h localhost -p 1883 -t myiot_local/salon/sensor/light -m '{"value":200,"unit":"lux","msg_id":"dup1"}'
sleep 0.5
mosquitto_pub -h localhost -p 1883 -t myiot_local/salon/sensor/light -m '{"value":200,"unit":"lux","msg_id":"dup1"}'

echo "Tests completed!"
