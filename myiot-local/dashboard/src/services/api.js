// -----------------------------------------------------------------------------
// CONFIGURATION (CHANGE THIS WHEN DEPLOYING TO LAB SERVER)
// -----------------------------------------------------------------------------
// LOCAL DOCKER: 'http://localhost:8000'
// LAB SERVER:   'http://192.168.1.1:8001' 
const API_BASE_URL = 'http://localhost:8000';
// -----------------------------------------------------------------------------

/**
 * Fetches the latest sensor measurements from the Lab Server.
 * Endpoint: GET /measurements
 */
export const fetchMeasurements = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/measurements`);
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch measurements:", error);
        return null;
    }
};

/**
 * Fetches all devices (Sensors, etc.)
 * Endpoint: GET /devices
 */
export const fetchDevices = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/devices`);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch devices:", error);
        return [];
    }
};

/**
 * Fetches all actuators (Lamps, Motors, etc.)
 * Endpoint: GET /actuators
 */
export const fetchActuators = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/actuators`);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch actuators:", error);
        return [];
    }
};

/**
 * Fetches measurement counts per device (active sensor types)
 * Endpoint: GET /stats/sensor_counts
 */
export const fetchSensorCounts = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/stats/sensor_counts`);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch sensor counts:", error);
        return {};
    }
};

/**
 * Fetches the latest measurement value for a specific device and sensor type.
 * Endpoint: GET /measurements/{device_id}/{sensor_type}?limit=1
 */
export const fetchLatestSensorValue = async (deviceId, sensorType) => {
    try {
        const response = await fetch(`${API_BASE_URL}/measurements/${deviceId}/${sensorType}?limit=1`);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        const data = await response.json();
        return data.length > 0 ? data[0] : null;
    } catch (error) {
        console.error(`Failed to fetch ${sensorType} for ${deviceId}:`, error);
        return null;
    }
};

/**
 * Fetches historical sensor measurements for a chart.
 * Endpoint: GET /measurements/{device_id}/{sensor_type}?limit={limit}
 */
export const fetchSensorHistory = async (deviceId, sensorType, limit = 20) => {
    try {
        const response = await fetch(`${API_BASE_URL}/measurements/${deviceId}/${sensorType}?limit=${limit}`);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch history for ${sensorType}:`, error);
        return [];
    }
};

/**
 * Fetches all users (members)
 * Endpoint: GET /users
 */
export const fetchUsers = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/users`);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch users:", error);
        return [];
    }
};

/**
 * Registers a new user
 * Endpoint: POST /register
 */
export const registerUser = async (userData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `API Error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to register user:", error);
        throw error;
    }
};

