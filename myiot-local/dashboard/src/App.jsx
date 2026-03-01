import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './App.css'
import Dashboard from './pages/Dashboard'
import HistoryPage from './pages/HistoryPage'
import LoginPage from './pages/LoginPage'
import ProtectedRoute from './components/ProtectedRoute'
import MembersPage from './pages/MembersPage'
import DevicesPage from './pages/DevicesPage'
import { fetchDevices, toggleDevice as apiToggleDevice } from './services/api'
import { ROOM_MAPPING, SENSOR_CONFIG, ALLOWED_TYPES } from './constants'

function App() {
  const [devices, setDevices] = useState([]);

  // Fetch and Configure Devices
  useEffect(() => {
    const loadDevices = async () => {
      try {
        const apiDevices = await fetchDevices();
        if (apiDevices && apiDevices.length > 0) {

          // Flatten device sensors into a single list
          const flatList = [];

          apiDevices.forEach(d => {
            const sensorTypes = d.sensor_types || [];

            sensorTypes.forEach(type => {
              const lowerType = type.toLowerCase();

              // Filter by allowed types (defined in constants)
              if (ALLOWED_TYPES.includes(lowerType)) {

                const roomName = d.location || 'Unknown Room';

                // Get config for icon and color, or use default
                const config = SENSOR_CONFIG[lowerType] || { name: `${type} Sensor`, icon: SENSOR_CONFIG.default.icon, color: SENSOR_CONFIG.default.color };

                // Check if sensor is active
                const isActive = (d.sensor_states && d.sensor_states[type] !== undefined)
                  ? d.sensor_states[type]
                  : true;

                flatList.push({
                  id: d.device_id,
                  uniqueId: `${d.device_id}_${type}`,
                  name: config.name,
                  status: `${isActive ? 'Active' : 'Inactive'} - ${roomName}`,
                  isOn: isActive,
                  activeText: 'ON',
                  icon: config.icon,
                  color: config.color,
                  roomName: roomName
                });
              }
            });
          });

          // Store filtered list
          setDevices(flatList);
        }
      } catch (e) {
        console.error("Failed to load devices", e);
      }
    };
    loadDevices();
  }, []);

  const toggleDevice = (uniqueId) => {
    // Optimistic UI Update
    setDevices(prev => prev.map(d => {
      if (d.uniqueId === uniqueId) {
        const newState = !d.isOn;
        const newStatus = newState ? 'Active' : 'Inactive';
        return {
          ...d,
          isOn: newState,
          status: `${newStatus} - ${d.roomName}`,
        };
      }
      return d;
    }));

    // Find device and call API
    const device = devices.find(d => d.uniqueId === uniqueId);
    if (device) {
      apiToggleDevice(device.id).catch(err => console.error("Toggle failed", err));
    }
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              {/* Only show first 6 on Dashboard */}
              <Dashboard devices={devices.slice(0, 6)} toggleDevice={toggleDevice} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/devices"
          element={
            <ProtectedRoute>
              <DevicesPage devices={devices} toggleDevice={toggleDevice} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <HistoryPage />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/members"
          element={
            <ProtectedRoute>
              <MembersPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
