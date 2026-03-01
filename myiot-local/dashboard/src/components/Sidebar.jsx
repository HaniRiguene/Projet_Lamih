import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Sidebar.css';
import { LayoutDashboard, Wifi, Users, LogOut, History } from 'lucide-react';

export default function Sidebar() {
    const navigate = useNavigate();
    const location = useLocation();

    // Determine active menu item based on current path
    const getActiveItem = () => {
        const path = location.pathname;
        if (path === '/') return 'Dashboard';
        if (path === '/devices') return 'Devices';
        if (path === '/members') return 'Members';
        if (path === '/history') return 'History';
        return 'Dashboard';
    };

    const activeItem = getActiveItem();

    const menuItems = [
        { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={25} /> },
        { name: 'Devices', path: '/devices', icon: <Wifi size={25} /> },
        { name: 'Members', path: '/members', icon: <Users size={25} /> },
        { name: 'History', path: '/history', icon: <History size={25} /> },
    ];

    const handleNavigation = (item) => {
        navigate(item.path);
    };

    const handleLogout = (e) => {
        e.preventDefault();
        localStorage.removeItem('user');
        navigate('/login');
    };

    return (
        <div className="sidebar">
            <div className="logo-container">
                <h2 className="logo-text">MyHome</h2>
            </div>

            <ul className="nav-list">
                {menuItems.map((item) => (
                    <li
                        key={item.name}
                        className={`nav-item ${activeItem === item.name ? 'active' : ''}`}
                        onClick={() => handleNavigation(item)}
                    >
                        <a href="#" className="nav-link" onClick={(e) => e.preventDefault()}>
                            <span className="icon">{item.icon}</span>
                            <span className="title">{item.name}</span>
                        </a>
                    </li>
                ))}

                {/* Separator or Spacer */}
                <li style={{ marginTop: 'auto' }}></li>

                <li className="nav-item">
                    <a href="#" className="nav-link" onClick={handleLogout}>
                        <span className="icon"><LogOut size={20} /></span>
                        <span className="title">Logout</span>
                    </a>
                </li>
            </ul>
        </div>
    );
}
