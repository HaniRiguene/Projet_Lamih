import React from 'react';
import './DeviceCard.css';

// Component to display individual device information and control switch
export default function DeviceCard({ name, status, activeText, icon: Icon, iconColor, isOn, onToggle, disabled }) {
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

                {/* Switch Button Control */}
                <div
                    className={`toggle-switch ${isOn ? 'on' : ''}`}
                    onClick={() => !disabled && onToggle && onToggle()}
                    style={disabled ? { opacity: 0.5, cursor: 'not-allowed', filter: 'grayscale(100%)' } : {}}
                    title={disabled ? "Disabled for Guest users" : ""}
                >
                    <div className="toggle-knob"></div>
                </div>
            </div>
        </div>
    );
}
