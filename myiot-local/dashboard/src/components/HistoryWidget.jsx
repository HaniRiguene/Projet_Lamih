import React from 'react';
import { Smartphone, Router, Lightbulb, Cctv, Tv, Speaker } from 'lucide-react';
import { Link } from 'react-router-dom';
import './RightPanel.css';

const HistoryWidget = ({ historyItems }) => {
    // Mapping string status to style
    const renderStatus = (status) => {
        if (status === 'ON') return <span className="status-on">ON</span>;
        if (status === 'OFF') return <span className="status-off">OFF</span>;
        return status;
    };

    // Fallback if no props provided (though it should be)
    // const historyItems = props.historyItems || [];

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
