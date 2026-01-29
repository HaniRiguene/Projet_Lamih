"""
MyIoT API - Local REST API
Expose les données IoT (sensors, actuators) via HTTP
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5434'))
DB_NAME = os.getenv('DB_NAME', 'myiot_db')
DB_USER = os.getenv('DB_USER', 'myiot_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'myiot_pass')

# ==================== FastAPI Setup ====================

app = FastAPI(
    title="MyIoT API",
    description="API pour la stack MyIoT locale",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Database ====================

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# ==================== Pydantic Models ====================

class Device(BaseModel):
    device_id: str
    device_type: str
    location: Optional[str] = None
    created_at: str

class Measurement(BaseModel):
    device_id: str
    sensor_type: str
    value: float
    unit: str
    msg_id: str
    received_at: str

class Actuator(BaseModel):
    actuator_id: str
    actuator_type: str
    location: Optional[str] = None
    created_at: str

class ActuatorState(BaseModel):
    actuator_id: str
    state: str
    triggered_by: Optional[str] = None
    updated_at: str

# ==================== Routes ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "MyIoT API",
        "version": "1.0.0",
        "description": "API pour la stack MyIoT locale",
        "endpoints": {
            "devices": "/devices",
            "measurements": "/measurements",
            "actuators": "/actuators",
            "actuator_states": "/actuator_states",
            "sensor_data": "/sensor_data/{device_id}/{sensor_type}"
        }
    }

# ==================== DEVICES ====================

@app.get("/devices", response_model=List[Device])
async def get_devices():
    """Get all devices"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM devices ORDER BY device_id")
        devices = cursor.fetchall()
        cursor.close()
        return devices
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/devices/{device_id}")
async def get_device(device_id: str):
    """Get specific device"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM devices WHERE device_id = %s", (device_id,))
        device = cursor.fetchone()
        cursor.close()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching device: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ==================== MEASUREMENTS ====================

@app.get("/measurements", response_model=List[Measurement])
async def get_measurements(
    limit: int = Query(100, ge=1, le=1000),
    device_id: Optional[str] = None,
    sensor_type: Optional[str] = None
):
    """Get measurements with optional filters"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT * FROM measurements WHERE 1=1"
        params = []
        
        if device_id:
            query += " AND device_id = %s"
            params.append(device_id)
        
        if sensor_type:
            query += " AND sensor_type = %s"
            params.append(sensor_type)
        
        query += " ORDER BY received_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        measurements = cursor.fetchall()
        cursor.close()
        return measurements
    except Exception as e:
        logger.error(f"Error fetching measurements: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/measurements/{device_id}/{sensor_type}")
async def get_sensor_data(
    device_id: str,
    sensor_type: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get measurements for specific device and sensor"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM measurements WHERE device_id = %s AND sensor_type = %s ORDER BY received_at DESC LIMIT %s",
            (device_id, sensor_type, limit)
        )
        measurements = cursor.fetchall()
        cursor.close()
        return measurements
    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ==================== ACTUATORS ====================

@app.get("/actuators", response_model=List[Actuator])
async def get_actuators():
    """Get all actuators"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM actuators ORDER BY actuator_id")
        actuators = cursor.fetchall()
        cursor.close()
        return actuators
    except Exception as e:
        logger.error(f"Error fetching actuators: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ==================== ACTUATOR STATES ====================

@app.get("/actuator_states", response_model=List[ActuatorState])
async def get_actuator_states(
    limit: int = Query(100, ge=1, le=1000),
    actuator_id: Optional[str] = None
):
    """Get actuator states"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT * FROM actuator_states WHERE 1=1"
        params = []
        
        if actuator_id:
            query += " AND actuator_id = %s"
            params.append(actuator_id)
        
        query += " ORDER BY updated_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        states = cursor.fetchall()
        cursor.close()
        return states
    except Exception as e:
        logger.error(f"Error fetching actuator states: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ==================== STATISTICS ====================

@app.get("/stats")
async def get_statistics():
    """Get database statistics"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Count devices
        cursor.execute("SELECT COUNT(*) as count FROM devices")
        device_count = cursor.fetchone()['count']
        
        # Count measurements
        cursor.execute("SELECT COUNT(*) as count FROM measurements")
        measurement_count = cursor.fetchone()['count']
        
        # Count actuators
        cursor.execute("SELECT COUNT(*) as count FROM actuators")
        actuator_count = cursor.fetchone()['count']
        
        # Sensor types
        cursor.execute("SELECT sensor_type, COUNT(*) as count FROM measurements GROUP BY sensor_type")
        sensor_types = cursor.fetchall()
        
        # Latest measurement
        cursor.execute("SELECT received_at FROM measurements ORDER BY received_at DESC LIMIT 1")
        latest = cursor.fetchone()
        
        cursor.close()
        
        return {
            "devices": device_count,
            "measurements": measurement_count,
            "actuators": actuator_count,
            "sensor_types": sensor_types,
            "latest_measurement": latest['received_at'] if latest else None
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ==================== HEALTH ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
    finally:
        conn.close()

# ==================== ERROR HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
