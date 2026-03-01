import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchSensorHistory } from '../services/api';
import './SensorInfoCard.css';

const LightIntensityChart = ({ deviceId }) => {
    const [chartData, setChartData] = useState([]);

    useEffect(() => {
        const loadHistory = async () => {
            if (!deviceId) {
                setChartData([]);
                return;
            }

            // Fetch history for both sensors
            // Get slightly more data to ensure we have enough points for the chart
            const [tempHistory, lumHistory] = await Promise.all([
                fetchSensorHistory(deviceId, 'temperature', 10),
                fetchSensorHistory(deviceId, 'luminosity', 10)
            ]);

            // Merge data arrays
            // The API returns data newest-first, so time flows backwards in the array.
            // We iterate through both arrays and pair them up by index for the chart.

            const maxLen = Math.max((tempHistory || []).length, (lumHistory || []).length);
            const formattedData = [];

            for (let i = 0; i < maxLen; i++) {
                const t = (tempHistory || [])[i];
                const l = (lumHistory || [])[i];

                // Determine time label: prioritize the LATEST timestamp among the pair
                let refTime = null;
                if (t && l) {
                    // Compare timestamps string (works for ISO) or Date
                    const tDate = new Date(t.received_at);
                    const lDate = new Date(l.received_at);
                    refTime = (tDate > lDate) ? t.received_at : l.received_at;
                } else if (t) {
                    refTime = t.received_at;
                } else if (l) {
                    refTime = l.received_at;
                }

                let timeStr = `T-${i}`;
                if (refTime) {
                    const date = new Date(refTime);
                    if (!isNaN(date)) {
                        // Add 1 Hour offset as requested
                        date.setHours(date.getHours() + 1);
                        timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    }
                }

                formattedData.push({
                    time: timeStr,
                    temp: t ? parseFloat(t.value) : null,
                    lum: l ? parseFloat(l.value) : null
                });
            }

            // Reverse to Chronological Order (Oldest -> Newest)
            setChartData(formattedData.reverse());
        };

        loadHistory();
        // Poll for updates every 5s
        const interval = setInterval(loadHistory, 2000);
        return () => clearInterval(interval);
    }, [deviceId]);

    return (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
            {/* Active Status Badge - Top Left reuse styles but override position */}
            {/* Online/Offline Status Badge - Top Left reuse styles but override position */}
            {chartData.length > 0 ? (
                <div className="sensor-status-badge" style={{ top: '-15px', right: 'auto', left: -10 }}>
                    <div className="status-dot"></div>
                    Online
                </div>
            ) : (
                <div className="sensor-status-badge inactive" style={{ top: '-15px', right: 'auto', left: -10 }}>
                    <div className="status-dot inactive"></div>
                    Offline
                </div>
            )}
            {/* Custom Legend - Top Right */}
            <div style={{
                position: 'absolute',
                top: '-15px',
                right: 0,
                zIndex: 10,
                paddingBottom: '5px'
            }}>
                <div style={{ display: 'flex', gap: '10px', fontSize: '12px', position: 'relative', top: '3px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#ff4757', boxShadow: '0 0 5px #ff4757' }}></span>
                        <span style={{ color: '#555' }}>Temperature</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#f1c40f', boxShadow: '0 0 5px #f1c40f' }}></span>
                        <span style={{ color: '#555' }}>Luminosity</span>
                    </div>
                </div>
            </div>

            <ResponsiveContainer width="100%" height="115%">
                <AreaChart
                    data={chartData}
                    margin={{
                        top: 20,     /* Minimized top margin */
                        right: 10,  /* increased for label space */
                        left: 0,    /* Removed negative margin */
                        bottom: 0,
                    }}
                >
                    <defs>
                        <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ff4757" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#ff4757" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorLum" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f1c40f" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#f1c40f" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                    <XAxis
                        dataKey="time"
                        tick={{ fontSize: 10, fill: '#888' }}
                        axisLine={false}
                        tickLine={false}
                        interval={1} // Show more labels
                    />

                    {/* Left Axis: Temperature */}
                    <YAxis
                        yAxisId="left"
                        domain={['auto', 'auto']} // Auto scale
                        tick={{ fontSize: 10, fill: '#555' }}
                        axisLine={false}
                        tickLine={false}
                        width={42}
                        label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#333', fontSize: '10px', fontWeight: 500 }, offset: 3 }}
                    />

                    {/* Right Axis: Luminosity */}
                    <YAxis
                        yAxisId="right"
                        orientation="right"
                        domain={['auto', 'auto']} // Auto scale
                        tick={{ fontSize: 10, fill: '#555' }}
                        axisLine={false}
                        tickLine={false}
                        width={28}
                        label={{ value: 'Luminosity (Lux)', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#333', fontSize: '10px', fontWeight: 500 }, offset: -8 }}
                    />

                    <Tooltip
                        contentStyle={{ borderRadius: '10px', border: 'none', boxShadow: '0 4px 15px rgba(0,0,0,0.1)' }}
                        labelStyle={{ color: '#333', fontWeight: 'bold' }}
                    />

                    <Area
                        yAxisId="left"
                        type="monotone"
                        dataKey="temp"
                        stroke="#ff4757"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorTemp)"
                        animationDuration={1000}
                    />
                    <Area
                        yAxisId="right"
                        type="monotone"
                        dataKey="lum"
                        stroke="#f1c40f"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorLum)"
                        animationDuration={1000}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export default LightIntensityChart;
