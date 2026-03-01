import React from 'react';
import './RoomCard.css';

// Component to display room status and sensor count
export default function RoomCard({ name, count, icon: Icon, active, onClick }) {
    return (
        <div className={`room-card ${active ? 'active' : ''}`} onClick={onClick}>
            <div className="room-card-header">
                <div className="icon-box">
                    <Icon size={20} />
                </div>
                <span className="room-name">{name}</span>
            </div>

            <div className="device-count">
                {count} Sensors
            </div>
        </div>
    );
}
