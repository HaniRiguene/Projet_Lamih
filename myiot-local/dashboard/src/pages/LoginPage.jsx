import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';
import smartHomeImg from '../assets/smart-home.png';

const LoginPage = () => {
    const [showPassword, setShowPassword] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    const [error, setError] = useState('');
    const [isShaking, setIsShaking] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');

        try {
            const response = await fetch('http://localhost:8000/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Login successful:', data);
                // Store user info and role
                localStorage.setItem('user', JSON.stringify(data));
                navigate('/');
            } else {
                triggerError('Invalid email or password');
            }
        } catch (error) {
            console.error('Login error:', error);
            triggerError('An error occurred during login');
        }
    };

    const triggerError = (msg) => {
        setError(msg);
        setIsShaking(true);
        setTimeout(() => setIsShaking(false), 500);
    };

    return (
        <div className="login-container">
            {/* Left Side: Brand & Visual */}
            <div className="login-left">
                <div className="brand-logo">MyHome</div>

                <div className="welcome-content">
                    <h1>Welcome to your Smart Home.</h1>
                    <p>Control everything from one place.</p>

                    {/* 3D Image */}
                    <div className="illustration-placeholder">
                        {console.log("Image Path:", smartHomeImg)}
                        <img
                            src={smartHomeImg}
                            alt="Smart Home Illustration"
                            className="illustration-img"
                            onError={(e) => {
                                console.error("Image failed to load", e);
                                e.target.style.display = 'none'; // Hide broken image icon
                                e.target.parentElement.innerText = "Image Failed to Load";
                            }}
                        />
                    </div>
                </div>
            </div>

            {/* Right Side: Login Form Card */}
            <div className="login-right">
                <div className="login-card">
                    <div className="login-header">
                        <div className="brand-logo-right">MyHome</div>
                        <h2>Welcome Back</h2>
                        <p className="login-subtitle">Please enter your details.</p>
                    </div>

                    <form onSubmit={handleLogin} className={isShaking ? 'shake' : ''}>
                        <div className={`input-group ${error ? 'input-error' : ''}`}>
                            <Mail className="input-icon" size={18} />
                            <input
                                type="email"
                                placeholder="Email"
                                className="form-input"
                                value={email}
                                onChange={(e) => {
                                    setEmail(e.target.value);
                                    setError('');
                                }}
                                required
                            />
                        </div>

                        <div className={`input-group ${error ? 'input-error' : ''}`}>
                            <Lock className="input-icon" size={18} />
                            <input
                                type={showPassword ? "text" : "password"}
                                placeholder="Password"
                                className="form-input"
                                value={password}
                                onChange={(e) => {
                                    setPassword(e.target.value);
                                    setError('');
                                }}
                                required
                            />
                            <div
                                className="toggle-password"
                                onClick={() => setShowPassword(!showPassword)}
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </div>
                        </div>

                        <label className="remember-me">
                            <input type="checkbox" />
                            <span>Remember me</span>
                        </label>

                        <button type="submit" className="login-btn">
                            Log In
                        </button>

                        {error && <div className="error-text">{error}</div>}
                    </form>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
