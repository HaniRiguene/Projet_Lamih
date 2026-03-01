import React, { useState, useEffect } from 'react';
import { ChevronRight, ChevronDown, Search, Cctv, Tv, Router, Smartphone, Speaker, Lightbulb } from 'lucide-react';
import { Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { fetchHistory, fetchDevices } from '../services/api';
import { SENSOR_CONFIG } from '../constants';
import '../App.css';
import '../components/RightPanel.css';

const HistoryPage = () => {
    const [historyItems, setHistoryItems] = useState([]);
    const [devices, setDevices] = useState([]);

    useEffect(() => {
        const loadData = async () => {
            // Fetch history and devices
            const [historyData, devicesData] = await Promise.all([
                fetchHistory(500),
                fetchDevices()
            ]);

            setDevices(devicesData);

            // Process history items to display correct names and icons
            const mappedData = historyData.map(item => {
                let displayName = item.device;
                let icon = Cctv;

                // Determine display name based on sensor type or ID
                if (item.device.includes('_')) {
                    const parts = item.device.split('_');
                    const type = parts[parts.length - 1].toLowerCase();

                    // Check config for match
                    if (SENSOR_CONFIG[type]) {
                        displayName = SENSOR_CONFIG[type].name;
                        icon = SENSOR_CONFIG[type].icon;
                    } else {
                        displayName = type.charAt(0).toUpperCase() + type.slice(1);
                    }
                } else {
                    displayName = item.device.charAt(0).toUpperCase() + item.device.slice(1);
                }

                return {
                    ...item,
                    icon: icon,
                    device: displayName,
                    time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    user: item.user_name
                };
            });
            setHistoryItems(mappedData);
        };
        loadData();
    }, []);

    // Filter State
    const [dateRange, setDateRange] = useState('All Time');
    const [selectedDevice, setSelectedDevice] = useState('All');
    const [selectedEvent, setSelectedEvent] = useState('All');

    // Reset page to 1 when filters change
    useEffect(() => {
        setCurrentPage(1);
    }, [dateRange, selectedDevice, selectedEvent]);

    // Apply filters to history items
    const filteredHistory = historyItems.filter(item => {
        if (selectedDevice !== 'All' && item.device !== selectedDevice) return false;
        if (selectedEvent !== 'All' && item.status !== selectedEvent) return false;

        if (!item.timestamp) return true;
        const diffTime = new Date() - new Date(item.timestamp);
        const diffHours = diffTime / (1000 * 60 * 60);

        if (dateRange === 'Last 24 Hours') return diffHours <= 24;
        if (dateRange === 'Last 7 Days') return diffHours <= 24 * 7;
        return true;
    });

    // Pagination Logic
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 8;

    // Calculate total pages
    const totalPages = Math.ceil(filteredHistory.length / itemsPerPage);

    // Get current items
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    const currentItems = filteredHistory.slice(indexOfFirstItem, indexOfLastItem);

    // Change page
    const paginate = (pageNumber) => setCurrentPage(pageNumber);
    const nextPage = () => setCurrentPage(prev => Math.min(prev + 1, totalPages));
    const prevPage = () => setCurrentPage(prev => Math.max(prev - 1, 1));

    // Helper to format date
    const formatDate = (isoString, timeStr) => {
        if (!isoString) return `Today, ${timeStr}`; // Fallback for old items

        const date = new Date(isoString);
        const now = new Date();
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);

        const isToday = date.toDateString() === now.toDateString();
        const isYesterday = date.toDateString() === yesterday.toDateString();

        if (isToday) return `Today, ${timeStr}`;
        if (isYesterday) return `Yesterday, ${timeStr}`;

        // Return structured date for older items (e.g. "Feb 10, 14:30")
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ', ' + timeStr;
    };

    // Helper to render status style
    const renderStatus = (status) => {
        if (status === 'ON') return <span style={{
            backgroundColor: 'rgba(39, 174, 96, 0.15)',
            color: '#27ae60',
            padding: '4px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: '600'
        }}>ON</span>;

        if (status === 'OFF') return <span style={{
            backgroundColor: 'rgba(255, 63, 52, 0.15)',
            color: '#ff3f34',
            padding: '4px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: '600'
        }}>OFF</span>;
        return status;
    };

    // Get unique devices
    const uniqueDevices = ['All', ...[...new Set(historyItems.map(item => item.device))].sort()];

    return (
        <div className="app-container">
            <Sidebar />

            <div className="main-content" style={{ padding: '30px 40px', backgroundColor: '#f3f4f6' }}>
                {/* Breadcrumb */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '25px', fontSize: '14px', color: '#666' }}>
                    <Link to="/" style={{ textDecoration: 'none', color: '#666' }}>My Home</Link>
                    <ChevronRight size={16} />
                    <span style={{ color: '#222', fontWeight: '500' }}>History</span>
                </div>

                {/* Main Card */}
                <div style={{ backgroundColor: 'white', borderRadius: '25px', padding: '30px 30px 20px 30px', boxShadow: '0 4px 20px rgba(0,0,0,0.03)', minHeight: '40vh', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ flex: 1 }}>
                        <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#273c75', marginBottom: '25px', marginTop: '-10px' }}>Activity History</h1>

                        {/* Filters Row */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginBottom: '30px', marginTop: '-10px' }}>
                            {/* Date Range */}
                            <div style={{ flex: 1, minWidth: '150px' }}>
                                <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '8px', color: '#222' }}>Date Range</label>
                                <div style={{ position: 'relative' }}>
                                    <select
                                        value={dateRange}
                                        onChange={(e) => setDateRange(e.target.value)}
                                        style={{ width: '100%', padding: '10px 15px', borderRadius: '10px', border: '1px solid #e0e0e0', appearance: 'none', color: '#444', outline: 'none', cursor: 'pointer' }}
                                    >
                                        <option value="All Time">All Time</option>
                                        <option value="Last 24 Hours">Last 24 Hours</option>
                                        <option value="Last 7 Days">Last 7 Days</option>
                                    </select>
                                    <ChevronDown size={16} style={{ position: 'absolute', right: '15px', top: '50%', transform: 'translateY(-50%)', color: '#888', pointerEvents: 'none' }} />
                                </div>
                            </div>

                            {/* Device Type */}
                            <div style={{ flex: 1, minWidth: '150px' }}>
                                <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '8px', color: '#222' }}>Device Type</label>
                                <div style={{ position: 'relative' }}>
                                    <select
                                        value={selectedDevice}
                                        onChange={(e) => setSelectedDevice(e.target.value)}
                                        style={{ width: '100%', padding: '10px 15px', borderRadius: '10px', border: '1px solid #e0e0e0', appearance: 'none', color: '#444', outline: 'none', cursor: 'pointer' }}
                                    >
                                        {uniqueDevices.map((device, index) => (
                                            <option key={index} value={device}>{device}</option>
                                        ))}
                                    </select>
                                    <ChevronDown size={16} style={{ position: 'absolute', right: '15px', top: '50%', transform: 'translateY(-50%)', color: '#888', pointerEvents: 'none' }} />
                                </div>
                            </div>

                            {/* Event Type */}
                            <div style={{ flex: 1, minWidth: '150px' }}>
                                <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '8px', color: '#222' }}>Event Type</label>
                                <div style={{ position: 'relative' }}>
                                    <select
                                        value={selectedEvent}
                                        onChange={(e) => setSelectedEvent(e.target.value)}
                                        style={{ width: '100%', padding: '10px 15px', borderRadius: '10px', border: '1px solid #e0e0e0', appearance: 'none', color: '#444', outline: 'none', cursor: 'pointer' }}
                                    >
                                        <option>All</option>
                                        <option>ON</option>
                                        <option>OFF</option>
                                    </select>
                                    <ChevronDown size={16} style={{ position: 'absolute', right: '15px', top: '50%', transform: 'translateY(-50%)', color: '#888', pointerEvents: 'none' }} />
                                </div>
                            </div>

                            {/* User */}
                            <div style={{ flex: 1, minWidth: '150px' }}>
                                <label style={{ display: 'block', fontSize: '13px', fontWeight: 'bold', marginBottom: '8px', color: '#222' }}>User</label>
                                <div style={{ position: 'relative' }}>
                                    <select style={{ width: '100%', padding: '10px 15px', borderRadius: '10px', border: '1px solid #e0e0e0', appearance: 'none', color: '#444', outline: 'none', cursor: 'pointer' }}>
                                        <option>All</option>
                                        <option>Hamid Jlabanda</option>
                                        <option>Mohamed</option>
                                    </select>
                                    <ChevronDown size={16} style={{ position: 'absolute', right: '15px', top: '50%', transform: 'translateY(-50%)', color: '#888', pointerEvents: 'none' }} />
                                </div>
                            </div>
                        </div>

                        {/* Table Header */}
                        <div style={{ display: 'flex', backgroundColor: '#f8f9fa', padding: '15px 20px', borderRadius: '10px', marginTop: '-20px' }}>
                            <div style={{ flex: 2, fontSize: '14px', fontWeight: '600', color: '#555' }}>Device</div>
                            <div style={{ flex: 1.5, fontSize: '14px', fontWeight: '600', color: '#555' }}>Event</div>
                            <div style={{ flex: 2, fontSize: '14px', fontWeight: '600', color: '#555' }}>User</div>
                            <div style={{ flex: 1.5, fontSize: '14px', fontWeight: '600', color: '#666', textAlign: 'right' }}>Date & Time</div>
                        </div>

                        {/* History Items List (Paginated) */}
                        <div className="history-list-full">
                            {currentItems.length === 0 ? (
                                <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>No history available</div>
                            ) : (
                                currentItems.map((item, index) => (
                                    <div key={index} style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        padding: '13px 20px',
                                        borderBottom: '1px solid #f0f0f0',
                                        transition: 'background-color 0.2s'
                                    }}
                                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#fafafa'}
                                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                                    >
                                        <div style={{ flex: 2, display: 'flex', alignItems: 'center', gap: '12px' }}>
                                            <div style={{
                                                width: '40px', height: '40px',
                                                borderRadius: '10px',
                                                backgroundColor: '#eef2ff',
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                color: '#4865ff'
                                            }}>
                                                <item.icon size={20} />
                                            </div>
                                            <span style={{ fontWeight: '500', color: '#222' }}>{item.device}</span>
                                        </div>

                                        <div style={{ flex: 1.5 }}>
                                            {renderStatus(item.status)}
                                        </div>

                                        <div style={{ flex: 2, color: '#444', fontSize: '14px' }}>
                                            by {item.user}
                                        </div>

                                        <div style={{ flex: 1.5, textAlign: 'right', color: '#666', fontSize: '14px' }}>
                                            {formatDate(item.timestamp, item.time)}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Pagination Controls */}
                    {totalPages > 1 && (
                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: '20px', gap: '10px' }}>
                            <button
                                onClick={prevPage}
                                disabled={currentPage === 1}
                                style={{
                                    padding: '8px 16px',
                                    borderRadius: '8px',
                                    border: '1px solid #e0e0e0',
                                    backgroundColor: currentPage === 1 ? '#f9fafb' : 'white',
                                    color: currentPage === 1 ? '#ccc' : '#444',
                                    cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                                    fontSize: '14px'
                                }}
                            >
                                Previous
                            </button>

                            {[...Array(totalPages)].map((_, i) => (
                                <button
                                    key={i}
                                    onClick={() => paginate(i + 1)}
                                    style={{
                                        width: '36px',
                                        height: '36px',
                                        borderRadius: '8px',
                                        border: currentPage === i + 1 ? 'none' : '1px solid #e0e0e0',
                                        backgroundColor: currentPage === i + 1 ? '#4361ee' : 'white',
                                        color: currentPage === i + 1 ? 'white' : '#444',
                                        cursor: 'pointer',
                                        fontWeight: '600',
                                        fontSize: '14px',
                                        transition: 'all 0.2s',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                    }}
                                >
                                    {i + 1}
                                </button>
                            ))}

                            <button
                                onClick={nextPage}
                                disabled={currentPage === totalPages}
                                style={{
                                    padding: '8px 16px',
                                    borderRadius: '8px',
                                    border: '1px solid #e0e0e0',
                                    backgroundColor: currentPage === totalPages ? '#f9fafb' : 'white',
                                    color: currentPage === totalPages ? '#ccc' : '#444',
                                    cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                                    fontSize: '14px'
                                }}
                            >
                                Next
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default HistoryPage;
