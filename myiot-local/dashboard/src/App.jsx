import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './App.css'
import Dashboard from './pages/Dashboard'
import HistoryPage from './pages/HistoryPage'
import LoginPage from './pages/LoginPage'
import ProtectedRoute from './components/ProtectedRoute'
import { Cctv, Tv, Router, Smartphone, Speaker, Lightbulb } from 'lucide-react'

function App() {

  // Static Config for Devices (Icons are functions, cannot be JSON stringified)
  const DEVICE_CONFIG = [
    { id: 1, name: 'Sensor 1', icon: Cctv, color: '#4865ff' },
    { id: 2, name: 'Sensor 2', icon: Tv, color: '#44bd32' },
    { id: 3, name: 'Sensor 3', icon: Router, color: '#fbc531' },
    { id: 4, name: 'Sensor 4', icon: Smartphone, color: '#ff3f34' },
    { id: 5, name: 'Sensor 5', icon: Speaker, color: '#e67e22' },
    { id: 6, name: 'Sensor 6', icon: Lightbulb, color: '#3498db' },
  ];

  // State for Recent Devices (Initialize from localStorage but merge with Config for Icons)
  const [devices, setDevices] = useState(() => {
    const saved = localStorage.getItem('dashboard_devices');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Merge saved state (isOn, status) with Config (Icon, Name, Color)
        return DEVICE_CONFIG.map(config => {
          const savedState = parsed.find(p => p.id === config.id);
          return savedState ? { ...config, isOn: savedState.isOn, status: savedState.status || 'Active' } : { ...config, isOn: true, status: 'Active' };
        });
      } catch (e) {
        console.error("Failed to parse saved devices", e);
        return DEVICE_CONFIG.map(d => ({ ...d, isOn: true, status: 'Active' }));
      }
    }
    // Default State
    return DEVICE_CONFIG.map(d => ({ ...d, isOn: true, status: 'Active' }));
  });

  // Persist Devices (Only relevant state)
  useEffect(() => {
    const stateToSave = devices.map(({ id, isOn, status }) => ({ id, isOn, status }));
    localStorage.setItem('dashboard_devices', JSON.stringify(stateToSave));
  }, [devices]);

  // State for History (with LocalStorage)
  const [historyItems, setHistoryItems] = useState(() => {
    const saved = localStorage.getItem('dashboard_history');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Restore icons by matching device name to DEVICE_CONFIG
        return parsed.map(item => {
          const config = DEVICE_CONFIG.find(c => c.name === item.device);
          return { ...item, icon: config ? config.icon : Cctv }; // Fallback icon
        });
      } catch (e) {
        console.error("Failed to parse history", e);
      }
    }
    // Default History
    return [
      { device: 'Sensor 1', user: 'Hamid Jlabanda', status: 'ON', time: '14:52', icon: Cctv },
      { device: 'Sensor 2', user: 'Hamid Jlabanda', status: 'OFF', time: '13:29', icon: Tv },
      { device: 'Sensor 3', user: 'Hamid Jlabanda', status: 'ON', time: '12:43', icon: Router },
      { device: 'Sensor 4', user: 'Hamid Jlabanda', status: 'ON', time: '10:56', icon: Smartphone },
      { device: 'Sensor 5', user: 'Hamid Jlabanda', status: 'ON', time: '09:37', icon: Speaker },
    ];
  });

  // Persist History (Save plain object without icon function)
  useEffect(() => {
    // Cleanup: Remove items older than 7 days
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const validHistory = historyItems.filter(item => {
      const itemDate = new Date(item.timestamp || new Date().toISOString()); // Fallback for old items
      return itemDate > sevenDaysAgo;
    });

    // Only update if we actually filtered something out to avoid infinite loops
    if (validHistory.length !== historyItems.length) {
      setHistoryItems(validHistory);
    }

    const historyToSave = validHistory.map(({ icon, ...rest }) => rest);
    localStorage.setItem('dashboard_history', JSON.stringify(historyToSave));
  }, [historyItems]);

  const toggleDevice = (id) => {
    // 1. Find device in current state (closure) to update history FIRST
    const deviceToToggle = devices.find(d => d.id === id);

    if (deviceToToggle) {
      const newStatus = !deviceToToggle.isOn ? 'ON' : 'OFF';
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      const newHistoryItem = {
        device: deviceToToggle.name,
        user: 'Hamid Jlabanda',
        status: newStatus,
        time: timeStr, // Keep for display
        timestamp: now.toISOString(), // Add for filtering/sorting
        icon: deviceToToggle.icon
      };

      // Update history: Add new item, NO slicing here (we handle retention in useEffect/rendering)
      setHistoryItems(prevHistory => [newHistoryItem, ...prevHistory]);
    }

    // 2. Update device state
    setDevices(prevDevices => prevDevices.map(device =>
      device.id === id ? { ...device, isOn: !device.isOn } : device
    ));
  };








  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard devices={devices} toggleDevice={toggleDevice} historyItems={historyItems} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <HistoryPage historyItems={historyItems} />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
