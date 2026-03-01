import React from 'react';

// Simple header component for consistent layout across pages
export default function Header() {
    return (
        <header style={{
            backgroundColor: '#242424',
            padding: '1rem',
            borderBottom: '1px solid #444',
            marginBottom: '2rem'
        }}>
            <h1 style={{ margin: 0, fontSize: '1.5rem' }}>IoT Dashboard</h1>
        </header>
    );
}
