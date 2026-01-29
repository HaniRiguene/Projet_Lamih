import paho.mqtt.client as mqtt
import psycopg2
import json
import ast
import logging
import os
import time
from datetime import datetime
from topics_local import SENSORS_WILDCARD, parse_sensor_topic, actuator_topic, IOT_PREFIX

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'myiot_db')
DB_USER = os.getenv('DB_USER', 'myiot_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'myiot_pass')

# Global DB connection and MQTT client
db_conn = None
mqtt_client = None

# Automation rules state
last_action = {}

def init_db():
    """Initialize database connection with retry logic"""
    global db_conn
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            db_conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logger.info("Database connection established")
            return True
        except psycopg2.OperationalError as e:
            retry_count += 1
            logger.warning(f"DB connection failed (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                time.sleep(5)
            else:
                logger.error("Max retries reached for DB connection")
                return False

def publish_actuator_state(actuator_id, state, room=None):
    """Publish actuator state to MQTT"""
    try:
        # If room is provided, use per-room actuator topic
        if room:
            topic = actuator_topic(room, actuator_id, 'cmd')
        else:
            # fallback to room-agnostic actuator topic
            topic = f"{IOT_PREFIX}/actuator/{actuator_id}/cmd"

        payload = json.dumps({"state": state})
        mqtt_client.publish(topic, payload)
        logger.info(f"Published to {topic}: {payload}")
    except Exception as e:
        logger.error(f"Error publishing to MQTT: {e}")

def apply_automation_rules(device_id, sensor_type, value, location=None):
    """Apply automation rules based on sensor value"""
    # Rule 1: Button control (manual override)
    if sensor_type == "button":
        if value == 1:
            # Button pressed: Turn ON lamp for this room
            publish_actuator_state('lamp1', 'ON', room=location)
            logger.info(f"Automation triggered: Button pressed (room={location}) -> Lamp ON")
        else:
            # Button released: Turn OFF lamp
            publish_actuator_state('lamp1', 'OFF', room=location)
            logger.info(f"Automation triggered: Button released (room={location}) -> Lamp OFF")
    
    # Rule 2: Light sensor automation
    elif sensor_type == "light":
        rule_key = f"{location or 'noloc'}_{device_id}_light_automation"
        
        if value < 200:
            # Turn on lamp if not already on
            if last_action.get(rule_key) != "ON":
                publish_actuator_state('lamp1', 'ON', room=location)
                last_action[rule_key] = "ON"
                logger.info(f"Automation triggered: Light < 200 (value={value}) -> Lamp ON")
        
        elif value > 300:
            # Turn off lamp if not already off
            if last_action.get(rule_key) != "OFF":
                publish_actuator_state('lamp1', 'OFF', room=location)
                last_action[rule_key] = "OFF"
                logger.info(f"Automation triggered: Light > 300 (value={value}) -> Lamp OFF")
        
        else:
            logger.debug(f"Light value {value} in neutral zone (200-300), no action")

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker"""
    if rc == 0:
        logger.info("Automation connected to MQTT broker")
        client.subscribe(SENSORS_WILDCARD)
        logger.info(f"Subscribed to: {SENSORS_WILDCARD}")
    else:
        logger.error(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server"""
    try:
        topic = msg.topic
        raw = msg.payload.decode('utf-8')
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as ex:
            logger.debug(f"JSON decode error, raw payload: {raw}")
            s = raw.strip()
            if s.startswith("'") and s.endswith("'"):
                s = s[1:-1]
            try:
                payload = json.loads(s)
            except json.JSONDecodeError:
                try:
                    payload = ast.literal_eval(s)
                except Exception as e:
                    logger.debug(f"Attempting simple KV parse for raw: {raw}")
                    try:
                        s2 = s.strip()
                        if s2.startswith('{') and s2.endswith('}'):
                            inner = s2[1:-1]
                            parts_kv = [p.strip() for p in inner.split(',') if p.strip()]
                            payload = {}
                            for kv in parts_kv:
                                if ':' in kv:
                                    k, v = kv.split(':', 1)
                                    k = k.strip()
                                    v = v.strip()
                                    try:
                                        if '.' in v:
                                            payload[k] = float(v)
                                        else:
                                            payload[k] = int(v)
                                    except Exception:
                                        payload[k] = v.strip('"\'')
                            logger.info(f"Parsed simple KV payload: {payload}")
                        else:
                            logger.error(f"Failed to parse payload (raw): {raw} - {e}")
                            raise ex
                    except Exception as e2:
                        logger.error(f"Failed to parse payload (raw): {raw} - {e2}")
                        raise ex
        
        # New sensor topic format: myiot_local/<room>/sensor/<sensor_type>
        room, sensor_type = parse_sensor_topic(topic)
        if not room or not sensor_type:
            logger.warning(f"Invalid topic format (expected {IOT_PREFIX}/+/sensor/+): {topic}")
            return

        value = payload.get('value')
        if value is not None:
            logger.debug(f"Received: room={room}, sensor={sensor_type}, value={value}")
            apply_automation_rules(room, sensor_type, float(value), location=room)
        else:
            logger.warning(f"No 'value' in payload: {payload}")
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {msg.topic}: {e} -- raw: {msg.payload}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def main():
    """Main function"""
    global mqtt_client
    
    if not init_db():
        logger.error("Failed to initialize database. Exiting.")
        return
    
    # Create MQTT client
    mqtt_client = mqtt.Client(client_id="myiot_automation")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        logger.info(f"Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        mqtt_client.loop_forever()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        if db_conn:
            db_conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()
