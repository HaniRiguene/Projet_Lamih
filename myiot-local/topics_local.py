# Local topic helpers for myiot_local per-room format
import os
IOT_PREFIX = os.getenv('IOT_PREFIX', 'myiot_local')

# Wildcards
SENSORS_WILDCARD = f"{IOT_PREFIX}/+/sensor/+"
ACTUATOR_WILDCARD = f"{IOT_PREFIX}/+/actuator/+"

# Helpers
def sensor_topic(room: str, sensor: str) -> str:
    return f"{IOT_PREFIX}/{room}/sensor/{sensor}"

def actuator_topic(room: str, actuator_id: str, cmd_name: str = 'cmd') -> str:
    return f"{IOT_PREFIX}/{room}/actuator/{actuator_id}/{cmd_name}"

# Parsing
def parse_sensor_topic(topic: str):
    parts = topic.split('/')
    # Expected: [IOT_PREFIX, <room>, 'sensor', <sensor>]
    if len(parts) == 4 and parts[0] == IOT_PREFIX and parts[2] == 'sensor':
        return parts[1], parts[3]
    return (None, None)

def parse_actuator_topic(topic: str):
    parts = topic.split('/')
    # Expected: [IOT_PREFIX, <room>, 'actuator', <actuator_id>, <cmd>]
    if len(parts) >= 5 and parts[0] == IOT_PREFIX and parts[2] == 'actuator':
        return parts[1], parts[3], parts[4]
    return None
