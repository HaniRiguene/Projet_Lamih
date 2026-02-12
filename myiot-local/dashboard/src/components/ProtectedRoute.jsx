import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
    const user = localStorage.getItem('user');

    if (!user) {
        // If no user is found in local storage, redirect to login page
        return <Navigate to="/login" replace />;
    }

    // If user exists, render the child component (Dashboard, History, etc.)
    return children;
};

export default ProtectedRoute;
