import paho.mqtt.client as mqtt
import psycopg2
from psycopg2.extras import execute_values
import json
import ast
import logging
import os
from topics_local import SENSORS_WILDCARD, parse_sensor_topic, IOT_PREFIX
from datetime import datetime
import time

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

# Global DB connection
db_conn = None

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

def ensure_device_exists(device_id, device_type="sensor"):
    """Ensure device exists in database"""
    try:
        cursor = db_conn.cursor()
        # Insert device with optional location handling (keeps existing location if present)
        cursor.execute(
            """
            INSERT INTO devices (device_id, device_type)
            VALUES (%s, %s)
            ON CONFLICT (device_id) DO NOTHING
            """,
            (device_id, device_type)
        )
        db_conn.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error ensuring device exists: {e}")
        db_conn.rollback()

def insert_measurement(device_id, sensor_type, value, unit, msg_id):
    """Insert measurement into database"""
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO measurements (device_id, sensor_type, value, unit, msg_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (device_id, msg_id) DO NOTHING
            """,
            (device_id, sensor_type, value, unit, msg_id)
        )
        db_conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Inserted measurement: device={device_id}, sensor={sensor_type}, value={value}")
        else:
            logger.debug(f"Duplicate measurement ignored: device={device_id}, msg_id={msg_id}")
        cursor.close()
    except psycopg2.IntegrityError as e:
        logger.debug(f"Duplicate entry ignored: {e}")
        db_conn.rollback()
    except Exception as e:
        logger.error(f"Error inserting measurement: {e}")
        db_conn.rollback()

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker"""
    if rc == 0:
        logger.info("Ingestor connected to MQTT broker")
        # Subscribe to new per-room sensor wildcard
        client.subscribe(SENSORS_WILDCARD)
        logger.info(f"Subscribed to: {SENSORS_WILDCARD}")
    else:
        logger.error(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server"""
    try:
        topic = msg.topic
        raw = msg.payload.decode('utf-8')
        # Robust JSON parsing: try json, then strip single quotes, then ast.literal_eval
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as ex:
            # Log raw payload for debugging and try fallbacks
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
                    # Fallback parsing for simple {key:val,key2:val2} payloads (no quotes)
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
                                    # convert numeric
                                    try:
                                        if '.' in v:
                                            payload[k] = float(v)
                                        else:
                                            payload[k] = int(v)
                                        
                                    except Exception:
                                        # strip quotes if present
                                        payload[k] = v.strip('"\'')
                            logger.info(f"Parsed simple KV payload: {payload}")
                        else:
                            logger.error(f"Failed to parse payload (raw): {raw} - {e}")
                            raise ex
                    except Exception as e2:
                        logger.error(f"Failed to parse payload (raw): {raw} - {e2}")
                        raise ex
        
        # Expected topic format:
        # myiot_local/<room>/sensor/<sensor_type>
        # Parse new sensor topic format: myiot_local/<room>/sensor/<sensor_type>
        room, sensor_type = parse_sensor_topic(topic)
        if not room or not sensor_type:
            logger.warning(f"Invalid topic format (expected {IOT_PREFIX}/+/sensor/+): {topic}")
            return

        device_id = room  # map room to device_id in DB
        # Extract payload
        value = payload.get('value')
        unit = payload.get('unit', '')
        msg_id = payload.get('msg_id', f"{device_id}_{int(time.time()*1000)}")

        if value is not None:
            ensure_device_exists(device_id)
            insert_measurement(device_id, sensor_type, float(value), unit, msg_id)
        else:
            logger.warning(f"No 'value' in payload: {payload}")
            
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {msg.topic}: {e} -- raw: {msg.payload}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def main():
    """Main function"""
    if not init_db():
        logger.error("Failed to initialize database. Exiting.")
        return
    
    # Create MQTT client
    client = mqtt.Client(client_id="myiot_ingestor")
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        logger.info(f"Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_forever()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        if db_conn:
            db_conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()
