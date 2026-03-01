import React from 'react';
import './SensorInfoCard.css';
import { ChevronUp, ChevronDown } from 'lucide-react';

// Component to display sensor values (Temperature, Luminosity) with online status
export default function SensorInfoCard({ icon: Icon, color, label, value, unit }) {
    return (
        <div className="sensor-card">
            {value !== '--' ? (
                <div className="sensor-status-badge">
                    <div className="status-dot"></div>
                    Online
                </div>
            ) : (
                <div className="sensor-status-badge inactive">
                    <div className="status-dot inactive"></div>
                    Offline
                </div>
            )}
            <div className="sensor-info">
                <div className="sensor-icon-circle" style={{ backgroundColor: color }}>
                    <Icon size={20} />
                </div>
                <div>
                    <div className="sensor-label">{label}</div>
                    <div className="sensor-value">{value}{unit}</div>
                </div>
            </div>

            <div className="sensor-controls">
                <div className="control-btn">
                    <ChevronUp size={24} />
                </div>
                <div className="control-btn">
                    <ChevronDown size={24} />
                </div>
            </div>
        </div>
    );
}
