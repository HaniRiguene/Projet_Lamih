import React from 'react';
import { Link } from 'react-router-dom';
import './RightPanel.css';

// Widget to display the latest activity logs in the sidebar
const HistoryWidget = ({ historyItems }) => {

    // Helper to style status badges (ON/OFF)
    const renderStatus = (status) => {
        if (status === 'ON') return <span className="status-on">ON</span>;
        if (status === 'OFF') return <span className="status-off">OFF</span>;
        return status;
    };

    return (
        <div className="right-panel-widget history-widget">
            <div className="widget-header">
                <h3 className="widget-title">History</h3>
                <Link to="/history" className="view-all">View all</Link>
            </div>
            <div className="history-list">
                {historyItems.map((item, index) => (
                    <div key={index} className="history-item">
                        <div className="history-icon">
                            <item.icon size={22} color="#4865ff" />
                        </div>
                        <div className="history-content">
                            <div className="history-top">
                                <span className="history-device">{item.device}</span>
                                <span className="history-time">{item.time}</span>
                            </div>
                            <div className="history-detail">
                                {renderStatus(item.status)} by {item.user}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default HistoryWidget;
