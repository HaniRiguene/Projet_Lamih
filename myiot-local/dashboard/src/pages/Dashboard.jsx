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
import { fetchSensorCounts, fetchLatestSensorValue } from '../services/api'
import { Sofa, Bed, Utensils, Bath, Thermometer, Sun, User } from 'lucide-react'

const Dashboard = ({ devices, toggleDevice, historyItems }) => {
    // Mapping Database Device IDs to Dashboard Rooms
    const ROOM_MAPPING = {
        'salon': 'Living Room',
        'entree': 'Kitchen',
        'cuisine': 'Kitchen',
        'bureau': 'Bedroom',
        'chambre': 'Bedroom',
        'bedroom': 'Bedroom',
        'chambre1': 'Bathroom',
        'bathroom': 'Bathroom',
    };

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

    // Helper to find a device ID for the current room
    const getDeviceForRoom = (roomName) => {
        const reverseMapping = Object.keys(ROOM_MAPPING).filter(key => ROOM_MAPPING[key] === roomName);
        if (reverseMapping.includes('salon')) return 'salon';
        if (reverseMapping.includes('chambre')) return 'chambre';
        if (reverseMapping.includes('cuisine')) return 'entree';
        if (reverseMapping.includes('chambre1')) return 'chambre1';
        return reverseMapping.length > 0 ? reverseMapping[0] : null;
    };

    // Effect to update Temperature when Active Room changes
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

            // Independent Door/Sabotage/Battery Check
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

    // Static Rooms Structure with Dynamic Counts State
    const [rooms, setRooms] = useState([
        { name: 'Living Room', count: 0, icon: Sofa },
        { name: 'Bedroom', count: 0, icon: Bed },
        { name: 'Kitchen', count: 0, icon: Utensils },
        { name: 'Bathroom', count: 0, icon: Bath },
    ]);

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

    return (
        <div className="app-container">
            <Sidebar />
            <div className="main-content">
                <header className="dashboard-header">
                    <div>
                        <h1 style={{ color: '#222', margin: '0 0 5px 0', fontSize: '26px' }}>My Home</h1>
                        <p style={{ color: '#666', margin: 0, fontSize: '14px' }}>Hi {user?.full_name?.split(' ')[0] || 'Guest'}, Good Morning!</p>
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
                                        key={device.id}
                                        name={device.name}
                                        status={device.status}
                                        isOn={device.isOn}
                                        icon={device.icon}
                                        iconColor={device.color}
                                        activeText={device.activeText}
                                        onToggle={() => toggleDevice(device.id)}
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
                <HistoryWidget historyItems={historyItems.slice(0, 5)} />
            </div>
        </div >
    )
}

export default Dashboard
