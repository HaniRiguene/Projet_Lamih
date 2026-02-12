import React from 'react';
import './DeviceCard.css';

export default function DeviceCard({ name, status, activeText, icon: Icon, iconColor, isOn, onToggle }) {
    return (
        <div className="device-card">
            <div className="device-header">
                <div className="device-icon-box" style={{ backgroundColor: iconColor }}>
                    <Icon size={24} />
                </div>
                <div className="device-info">
                    <span className="device-name">{name}</span>
                    <span className="device-status">{status}</span>
                </div>
            </div>

            <div className="device-footer">
                <span className="status-label">{isOn ? (activeText || 'ON') : 'OFF'}</span>

                <div className={`toggle-switch ${isOn ? 'on' : ''}`} onClick={onToggle}>
                    <div className="toggle-knob"></div>
                </div>
            </div>
        </div>
    );
}
