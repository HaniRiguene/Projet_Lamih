import React, { useState, useEffect } from 'react'
import '../App.css'
import Sidebar from '../components/Sidebar'
import RoomCard from '../components/RoomCard'
import SensorInfoCard from '../components/SensorInfoCard'
import DeviceCard from '../components/DeviceCard'
import MembersWidget from '../components/MembersWidget'
import HistoryWidget from '../components/HistoryWidget'
import SecurityStatusWidget from '../components/SecurityStatusWidget'
import LightIntensityChart from '../components/LightIntensityChart'
import { fetchSensorCounts, fetchLatestSensorValue, fetchHistory, logHistory } from '../services/api'
import { Cctv, User, Thermometer, Sun } from 'lucide-react'
import { ROOM_MAPPING, ROOM_UI_CONFIG, SENSOR_CONFIG } from '../constants'

const Dashboard = ({ devices, toggleDevice }) => {
    // Initialize default states for room and sensors
    // We use the mappings from constants.js to ensure names match the database

    const [activeRoom, setActiveRoom] = useState('Living Room');
    const [temperature, setTemperature] = useState('--');
    const [luminosity, setLuminosity] = useState('--');
    const [doorStatus, setDoorStatus] = useState(null);
    const [sabotageStatus, setSabotageStatus] = useState(null);
    const [batteryStatus, setBatteryStatus] = useState(null);
    const [user, setUser] = useState({ full_name: 'Guest' });

    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (e) {
                console.error("Failed to parse user from local storage", e);
            }
        }
    }, []);

    // Helper function to find the main device ID associated with a room name
    // This is needed because the database uses IDs like 'salon' but we display 'Living Room'
    const getDeviceForRoom = (roomName) => {
        const reverseMapping = Object.keys(ROOM_MAPPING).filter(key => ROOM_MAPPING[key] === roomName);
        if (reverseMapping.includes('salon')) return 'salon';
        if (reverseMapping.includes('chambre')) return 'chambre';
        if (reverseMapping.includes('cuisine')) return 'entree';
        if (reverseMapping.includes('chambre1')) return 'chambre1';
        return reverseMapping.length > 0 ? reverseMapping[0] : null;
    };

    // Update environmental data for active room
    useEffect(() => {
        const updateRoomData = async () => {
            const deviceId = getDeviceForRoom(activeRoom);
            if (deviceId) {
                const tempData = await fetchLatestSensorValue(deviceId, 'temperature');
                setTemperature(tempData ? tempData.value : '--');

                const lumData = await fetchLatestSensorValue(deviceId, 'luminosity');
                setLuminosity(lumData ? lumData.value : '--');
            } else {
                setTemperature('--');
                setLuminosity('--');
            }

            // Monitor security sensors
            const roomDeviceIds = Object.keys(ROOM_MAPPING).filter(key => ROOM_MAPPING[key] === activeRoom);

            let foundDoor = null;
            for (const devId of roomDeviceIds) {
                const doorData = await fetchLatestSensorValue(devId, 'door');
                if (doorData) { foundDoor = doorData; break; }
            }
            setDoorStatus(foundDoor ? foundDoor.value : null);

            let foundSabotage = null;
            for (const devId of roomDeviceIds) {
                const sabData = await fetchLatestSensorValue(devId, 'door_sabotage');
                if (sabData) { foundSabotage = sabData; break; }
            }
            setSabotageStatus(foundSabotage ? foundSabotage.value : null);

            let foundBattery = null;
            for (const devId of roomDeviceIds) {
                const battData = await fetchLatestSensorValue(devId, 'battery_porte');
                if (battData) { foundBattery = battData; break; }
            }
            setBatteryStatus(foundBattery ? foundBattery.value : null);
        };

        updateRoomData();
        const interval = setInterval(updateRoomData, 2000);
        return () => clearInterval(interval);
    }, [activeRoom]);

    // Room status configuration
    const [rooms, setRooms] = useState(ROOM_UI_CONFIG.map(r => ({ ...r, count: 0 })));

    useEffect(() => {
        const loadCounts = async () => {
            const countsData = await fetchSensorCounts();
            const counts = { 'Living Room': 0, 'Bedroom': 0, 'Kitchen': 0, 'Bathroom': 0 };

            if (countsData) {
                Object.entries(countsData).forEach(([deviceId, count]) => {
                    const roomName = ROOM_MAPPING[deviceId.toLowerCase()];
                    if (roomName && counts.hasOwnProperty(roomName)) {
                        counts[roomName] += count;
                    }
                });
            }

            setRooms(prevRooms => prevRooms.map(room => ({
                ...room,
                count: counts[room.name] || 0
            })));
        };

        loadCounts();
        const interval = setInterval(loadCounts, 2000);
        return () => clearInterval(interval);
    }, []);

    // History data management
    const [recentHistory, setRecentHistory] = useState([]);

    const loadHistory = async () => {
        const data = await fetchHistory(5);
        // Map icons and names
        const mappedHistory = data.map(item => {
            // Match sensor context
            const deviceConfig = devices.find(d => d.uniqueId === item.device);

            // Format display name
            let displayName = item.device;
            if (deviceConfig) {
                // Use configured name
                displayName = deviceConfig.name;
            } else if (item.device.includes('_')) {
                // Format ID as name
                const parts = item.device.split('_');
                const type = parts[parts.length - 1];
                displayName = type.charAt(0).toUpperCase() + type.slice(1);
            }

            return {
                ...item,
                time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                user: item.user_name,
                device: displayName, // Display name
                icon: deviceConfig ? deviceConfig.icon : Cctv
            };
        });
        setRecentHistory(mappedHistory);
    };

    useEffect(() => {
        if (devices.length > 0) {
            loadHistory();
        }
    }, [devices]);

    const handleDeviceToggle = async (uniqueId) => {
        const device = devices.find(d => d.uniqueId === uniqueId);
        if (!device) return;

        // Update UI state
        toggleDevice(uniqueId);

        // Log action to database
        const newStatus = device.isOn ? 'OFF' : 'ON';
        const userName = user.full_name || 'Guest';
        await logHistory(device.uniqueId, userName, newStatus);

        // Refresh history
        await loadHistory();
    };

    return (
        <div className="app-container">
            <Sidebar />
            <div className="main-content">
                <header className="dashboard-header">
                    <div>
                        <h1 style={{ color: '#222', margin: '0 0 5px 0', fontSize: '26px' }}>Dashboard</h1>
                        <p style={{ color: '#666', margin: 0, fontSize: '14px' }}>Welcome back, {user?.full_name?.split(' ')[0] || 'Guest'} 👋</p>
                    </div>
                </header>

                <div className="rooms-grid">
                    {rooms.map((room) => (
                        <RoomCard
                            key={room.name}
                            name={room.name}
                            count={room.count}
                            icon={room.icon}
                            active={activeRoom === room.name}
                            onClick={() => setActiveRoom(room.name)}
                        />
                    ))}
                </div>

                <div className="bottom-content-grid">
                    <div className="left-column">
                        <div>
                            <h2 style={{ fontSize: '18px', fontWeight: 'bold', color: '#222', marginBottom: '10px' }}>Temperature & Luminosity Trends</h2>
                            <div style={{
                                backgroundColor: 'white',
                                borderRadius: '20px',
                                padding: '20px',
                                height: '220px',
                                boxShadow: '0 4px 15px rgba(0,0,0,0.05)',
                                boxSizing: 'border-box',
                                position: 'relative'
                            }}>
                                <LightIntensityChart deviceId={getDeviceForRoom(activeRoom)} />
                            </div>
                        </div>

                        <div>
                            <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#222', marginBottom: '10px' }}>Recent Devices</h2>
                            <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
                                {devices.map(device => (
                                    <DeviceCard
                                        key={device.uniqueId}
                                        name={device.name}
                                        status={device.status}
                                        isOn={device.isOn}
                                        icon={device.icon}
                                        iconColor={device.color}
                                        activeText={device.activeText}
                                        onToggle={() => handleDeviceToggle(device.uniqueId)}
                                        disabled={user?.role === 'Guest'}
                                    />
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="right-column">
                        <div>
                            <h2 style={{ fontSize: '18px', fontWeight: 'bold', color: '#222', marginBottom: '10px' }}>Quick Setting</h2>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                                <SensorInfoCard
                                    label="Temperature"
                                    value={temperature}
                                    unit="°C"
                                    icon={Thermometer}
                                    color="#ff9f43"
                                />
                                <SensorInfoCard
                                    label="Luminosity"
                                    value={luminosity}
                                    unit="lux"
                                    icon={Sun}
                                    color="#f1c40f"
                                />
                            </div>
                        </div>
                        <SecurityStatusWidget doorStatus={doorStatus} sabotageStatus={sabotageStatus} batteryStatus={batteryStatus} />
                    </div>
                </div>
            </div>

            <div className="right-sidebar-panel">
                <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: '10px', gap: '15px' }}>
                    <div style={{ position: 'relative' }}>
                        <div style={{
                            width: '50px',
                            height: '50px',
                            borderRadius: '50%',
                            backgroundColor: '#e2e8f0',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '2px solid white',
                            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
                        }}>
                            <User size={30} color="#64748b" />
                        </div>
                        <div style={{
                            position: 'absolute', bottom: '2px', right: '2px',
                            width: '12px', height: '12px', backgroundColor: '#44bd32',
                            borderRadius: '50%', border: '2px solid #f3f4f6'
                        }}></div>
                    </div>
                    <span style={{ fontWeight: '600', fontSize: '16px', color: '#222' }}>{user.full_name || 'Guest'}</span>
                </div>
                <MembersWidget />
                <HistoryWidget historyItems={recentHistory} />
            </div>
        </div >
    )
}

export default Dashboard
