import React from 'react';
import { DoorOpen, DoorClosed, Bell, BatteryFull, BatteryLow, Shield, Zap } from 'lucide-react';
import './SecurityStatusWidget.css';

const SecurityStatusWidget = ({ doorStatus, sabotageStatus, batteryStatus }) => {
    // Determine Door State
    const isDoorOpen = doorStatus === 1;
    const isDoorClosed = doorStatus === 0;

    // Determine Sabotage State
    const isSabotageSafe = sabotageStatus === 0;
    const isSabotageAlert = sabotageStatus === 1;

    // Default Door Props
    let doorColor = '#ccc';
    let doorText = '--';
    let DoorIcon = DoorOpen;
    let animationClass = '';
    // let textAnimationClass = ''; // Removed per request

    if (isDoorOpen) {
        doorColor = '#ff3f34'; // Red
        doorText = 'OPEN!';
        DoorIcon = DoorOpen;
        animationClass = 'alarm-active';
        // textAnimationClass = 'text-alarm-active'; // Removed per request
    } else if (isDoorClosed) {
        doorColor = '#27ae60'; // Green
        doorText = 'CLOSED';
        DoorIcon = DoorClosed;
    }

    // Default Sabotage Props
    let sabColor = '#ccc';
    let sabText = '--';
    let SabIcon = Shield; // Default to Shield (neutral)
    let sabAnimationClass = '';
    // let sabTextAnimationClass = ''; // Removed per request

    if (isSabotageAlert) {
        sabColor = '#ff3f34'; // Red
        sabText = 'ALERT!';
        SabIcon = Bell;
        sabAnimationClass = 'alarm-active';
        // sabTextAnimationClass = 'text-alarm-active'; // Removed per request
    } else if (isSabotageSafe) {
        sabColor = '#27ae60'; // Green
        sabText = 'SAFE';
        SabIcon = Shield;
    }

    // Determine Battery State
    let batteryColor = '#ccc'; // Default to Grey (No Data)
    let BatteryIcon = BatteryFull;
    let batteryText = 'Battery: --';
    let batteryTextColor = '#ccc'; // Grey text for no data

    if (batteryStatus !== null) {
        batteryText = `Battery: ${batteryStatus}%`;
        batteryColor = '#44bd32'; // Green (Active)
        batteryTextColor = '#222'; // Default black text

        if (parseInt(batteryStatus) < 40) {
            batteryColor = '#ff3f34'; // Red (Low)
            BatteryIcon = BatteryLow;
            batteryTextColor = '#ff3f34'; // Red text for warning
        }
    }

    return (
        <React.Fragment>
            <h3 style={{
                fontSize: '18px',
                fontWeight: 'bold',
                color: '#222',
                marginBottom: '-16px',
                position: 'relative',
                top: '-19px'
            }}>Security Status</h3>
            <div style={{
                backgroundColor: 'white',
                borderRadius: '20px',
                padding: '25px 25px 8px 25px', /* Reduce bottom padding */
                boxShadow: '0 4px 15px rgba(0,0,0,0.05)',
                marginTop: 'auto',
                position: 'relative' // Needed for absolute positioning of badge
            }}>
                {/* Active/Inactive Status Badge - Top Right */}
                {doorStatus !== null ? (
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
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '-25px', marginTop: '8px' }}>
                    {/* Main Door */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '5px', width: '80px', marginTop: '12px' }}>
                        <div className={animationClass} style={{
                            width: '50px',
                            height: '50px',
                            borderRadius: '50%',
                            backgroundColor: doorColor,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            transition: 'background-color 0.3s ease'
                        }}>
                            <DoorIcon size={28} />
                        </div>
                        <span style={{ fontSize: '13px', color: '#666' }}>Door</span>
                        <span style={{ fontSize: '16px', fontWeight: 'bold', color: doorColor }}>{doorText}</span>
                    </div>

                    {/* Sabotage */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '5px', width: '80px', marginTop: '12px' }}>
                        <div className={sabAnimationClass} style={{
                            width: '50px',
                            height: '50px',
                            borderRadius: '50%',
                            backgroundColor: sabColor,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            transition: 'background-color 0.3s ease'
                        }}>
                            <SabIcon size={24} />
                        </div>
                        <span style={{ fontSize: '13px', color: '#666' }}>Sabotage</span>
                        <span style={{ fontSize: '16px', fontWeight: 'bold', color: sabColor }}>{sabText}</span>
                    </div>
                </div>

                {/* Battery */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    fontWeight: '500',
                    fontSize: '14px',
                    marginTop: '40px',
                    color: batteryTextColor
                }}>
                    <BatteryIcon size={25} color={batteryColor} />
                    <span>{batteryText}</span>
                </div>
            </div>
        </React.Fragment>
    );
};

export default SecurityStatusWidget;
