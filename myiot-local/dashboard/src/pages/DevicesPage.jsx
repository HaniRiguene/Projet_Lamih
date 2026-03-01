import React, { useState } from 'react';
import { ChevronRight, Wifi } from 'lucide-react';
import { Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import DeviceCard from '../components/DeviceCard';
import '../App.css';

import { logHistory } from '../services/api'

const DevicesPage = ({ devices, toggleDevice }) => {
    // State to track which room is being filtered
    const [filter, setFilter] = useState('All');
    const [user, setUser] = useState({ full_name: 'Guest' });

    // Get the current user from local storage to log who is toggling devices
    React.useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (e) {
                console.error("Failed to parse user from local storage", e);
            }
        }
    }, []);

    const handleToggle = async (uniqueId) => {
        const device = devices.find(d => d.uniqueId === uniqueId);
        if (!device) return;

        // Update UI state
        toggleDevice(uniqueId);

        // Record the action in the database
        const newStatus = device.isOn ? 'OFF' : 'ON';
        const userName = user.full_name || 'Guest';
        await logHistory(device.uniqueId, userName, newStatus);
    };

    // List of devices to display based on the filter
    const filteredDevices = filter === 'All'
        ? devices
        : devices.filter(d => d.roomName === filter);

    const rooms = ['All', 'Living Room', 'Bedroom', 'Kitchen', 'Bathroom'];

    return (
        <div className="app-container">
            <Sidebar />

            <div className="main-content" style={{ padding: '30px 40px', backgroundColor: '#f3f4f6' }}>
                {/* Breadcrumb */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '25px', fontSize: '14px', color: '#666' }}>
                    <Link to="/" style={{ textDecoration: 'none', color: '#666' }}>My Home</Link>
                    <ChevronRight size={16} />
                    <span style={{ color: '#222', fontWeight: '500' }}>Devices</span>
                </div>

                {/* Main Card */}
                <div style={{ backgroundColor: 'white', borderRadius: '25px', padding: '30px', boxShadow: '0 4px 20px rgba(0,0,0,0.03)', minHeight: '60vh' }}>

                    {/* Header */}
                    <div style={{ marginBottom: '30px' }}>
                        <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#273c75', margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
                            Devices
                        </h1>

                        {/* Filter Pills */}
                        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                            {rooms.map(room => (
                                <button
                                    key={room}
                                    onClick={() => setFilter(room)}
                                    style={{
                                        padding: '8px 20px',
                                        backgroundColor: filter === room ? '#4361ee' : '#f3f4f6',
                                        color: filter === room ? 'white' : '#666',
                                        border: 'none',
                                        borderRadius: '20px',
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        cursor: 'pointer',
                                        boxShadow: filter === room ? '0 4px 10px rgba(67, 97, 238, 0.3)' : 'none',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    {room === 'All' ? 'All Devices' : room}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Devices Grid */}
                    <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                        {filteredDevices.length > 0 ? (
                            filteredDevices.map(device => (
                                <DeviceCard
                                    key={device.uniqueId}
                                    name={device.name}
                                    status={device.status}
                                    isOn={device.isOn}
                                    icon={device.icon}
                                    iconColor={device.color}
                                    activeText={device.activeText}
                                    onToggle={() => handleToggle(device.uniqueId)}
                                />
                            ))
                        ) : (
                            <div style={{ width: '100%', textAlign: 'center', padding: '40px', color: '#999' }}>
                                No devices found.
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DevicesPage;
