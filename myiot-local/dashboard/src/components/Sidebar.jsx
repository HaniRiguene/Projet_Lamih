import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Sidebar.css';
import { LayoutDashboard, Home, Wifi, Lock, Users, Settings, LogOut } from 'lucide-react';

export default function Sidebar() {
    const [activeItem, setActiveItem] = useState('Dashboard');
    const navigate = useNavigate();

    const menuItems = [
        { name: 'Dashboard', icon: <LayoutDashboard size={25} /> },
        { name: 'My Home', icon: <Home size={25} /> },
        { name: 'Devices', icon: <Wifi size={25} /> },
        { name: 'Privacy', icon: <Lock size={25} /> },
        { name: 'Members', icon: <Users size={25} /> },
        { name: 'Settings', icon: <Settings size={25} /> }

    ];

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
                        onClick={() => setActiveItem(item.name)}
                    >
                        <a href="#" className="nav-link">
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
