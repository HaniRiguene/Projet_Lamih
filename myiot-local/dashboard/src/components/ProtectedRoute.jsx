import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
    const user = localStorage.getItem('user');

    if (!user) {
        // Redirect to login if user is not authenticated
        return <Navigate to="/login" replace />;
    }

    // Render child component if authenticated
    return children;
};

export default ProtectedRoute;
