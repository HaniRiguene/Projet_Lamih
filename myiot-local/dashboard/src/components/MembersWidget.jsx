import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './RightPanel.css';
import { User, X, Check, Eye, EyeOff, Shield, UserX } from 'lucide-react';
import { fetchUsers, registerUser } from '../services/api';

// Widget to display and manage members (users)
const MembersWidget = () => {
    const [members, setMembers] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [newUser, setNewUser] = useState({
        full_name: '',
        email: '',
        role: 'Guest', // Default
        password: ''
    });
    const [currentUser, setCurrentUser] = useState(null);

    const loadMembers = async () => {
        const users = await fetchUsers();
        if (users) {
            setMembers(users);
        }
    };

    useEffect(() => {
        loadMembers();
        const userStr = localStorage.getItem('user');
        if (userStr) {
            try {
                const user = JSON.parse(userStr);
                setCurrentUser(user);
            } catch (e) {
                console.error("Error parsing user from local storage", e);
            }
        }
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setNewUser(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleRoleSelect = (roleName) => {
        setNewUser(prev => ({ ...prev, role: roleName }));
    };

    const handleAddMember = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await registerUser(newUser);

            // Clear form and refresh list
            setShowModal(false);
            setNewUser({ full_name: '', email: '', role: 'Guest', password: '' });
            await loadMembers();
        } catch (error) {
            console.error("Failed to add member", error);
            alert("Failed to add member: " + error.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="right-panel-widget">
            <div className="widget-header">
                <h3 className="widget-title">Members</h3>
                <Link to="/members" className="view-all">View all</Link>
            </div>
            <div className="members-card">
                <div className="member-list">
                    {members.slice(0, 5).map((member, index) => (
                        <div key={index} className="member-item">
                            <div className="member-avatar" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#e2e8f0' }}>
                                <User size={24} color="#64748b" />
                            </div>
                            <div className="member-info">
                                <h4>{member.full_name}</h4>
                                <p>{member.role}</p>
                            </div>
                        </div>
                    ))}
                    {members.length === 0 && <p style={{ textAlign: 'center', color: '#888', fontStyle: 'italic' }}>No members found.</p>}
                </div>
                <button
                    className="add-member-btn"
                    onClick={() => setShowModal(true)}
                    disabled={currentUser?.role === 'Guest'}
                    style={currentUser?.role === 'Guest' ? { backgroundColor: '#9ca3af', cursor: 'not-allowed', opacity: 0.7 } : {}}
                    title={currentUser?.role === 'Guest' ? "Guests cannot add members" : "Add new member"}
                >
                    Add member
                </button>
            </div>

            {/* Modal Overlay for Adding Members */}
            {showModal && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
                    backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
                }}>
                    <div style={{
                        backgroundColor: 'white', borderRadius: '24px', padding: '30px', width: '400px',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.2)', fontFamily: 'Poppins, sans-serif'
                    }}>
                        <div style={{ marginBottom: '20px' }}>
                            <h2 style={{ margin: '0 0 5px 0', fontSize: '22px', fontWeight: 'bold' }}>Add Member</h2>
                            <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>Create New Member Account</p>
                        </div>

                        <form onSubmit={handleAddMember} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                            {/* Full Name */}
                            <div>
                                <label style={{ fontSize: '14px', fontWeight: '600', color: '#333', display: 'block', marginBottom: '8px' }}>Full Name</label>
                                <input
                                    type="text"
                                    name="full_name"
                                    placeholder="Full Name"
                                    value={newUser.full_name}
                                    onChange={handleInputChange}
                                    required
                                    style={{
                                        width: '100%', padding: '12px', borderRadius: '12px',
                                        border: '1px solid #e2e8f0', boxSizing: 'border-box', fontSize: '14px', outline: 'none'
                                    }}
                                />
                            </div>

                            {/* Email Address */}
                            <div>
                                <label style={{ fontSize: '14px', fontWeight: '600', color: '#333', display: 'block', marginBottom: '8px' }}>Email Address</label>
                                <input
                                    type="email"
                                    name="email"
                                    placeholder="Email Address"
                                    value={newUser.email}
                                    onChange={handleInputChange}
                                    required
                                    style={{
                                        width: '100%', padding: '12px', borderRadius: '12px',
                                        border: '1px solid #e2e8f0', boxSizing: 'border-box', fontSize: '14px', outline: 'none'
                                    }}
                                />
                            </div>

                            {/* Password */}
                            <div>
                                <label style={{ fontSize: '14px', fontWeight: '600', color: '#333', display: 'block', marginBottom: '8px' }}>Password</label>
                                <div style={{ position: 'relative' }}>
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        name="password"
                                        placeholder="Password"
                                        value={newUser.password}
                                        onChange={handleInputChange}
                                        required
                                        style={{
                                            width: '100%', padding: '12px', paddingRight: '40px', borderRadius: '12px',
                                            border: '1px solid #e2e8f0', boxSizing: 'border-box', fontSize: '14px', outline: 'none'
                                        }}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        style={{
                                            position: 'absolute',
                                            right: '12px',
                                            top: '50%',
                                            transform: 'translateY(-50%)',
                                            background: 'none',
                                            border: 'none',
                                            cursor: 'pointer',
                                            color: '#94a3b8',
                                            padding: 0,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            width: '24px',
                                            height: '24px'
                                        }}
                                    >
                                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                </div>
                            </div>

                            {/* Role Selection */}
                            <div>
                                <label style={{ fontSize: '14px', fontWeight: '600', color: '#333', display: 'block', marginBottom: '8px' }}>Role</label>
                                <div style={{ display: 'flex', gap: '15px' }}>
                                    {/* Admin Card */}
                                    <div
                                        onClick={() => handleRoleSelect('Administrator')}
                                        style={{
                                            flex: 1,
                                            border: newUser.role === 'Administrator' ? '2px solid #536bf6' : '1px solid #e2e8f0',
                                            borderRadius: '16px',
                                            padding: newUser.role === 'Administrator' ? '15px' : '16px', // Adjust padding to maintain size
                                            cursor: 'pointer',
                                            backgroundColor: newUser.role === 'Administrator' ? '#eff6ff' : 'white',
                                            textAlign: 'center',
                                            transition: 'all 0.2s',
                                            boxSizing: 'border-box'
                                        }}
                                    >
                                        <div style={{
                                            backgroundColor: '#536bf6', width: '40px', height: '40px', borderRadius: '10px',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 10px auto', color: 'white'
                                        }}>
                                            <Shield size={20} />
                                        </div>
                                        <h4 style={{ margin: '0 0 5px 0', fontSize: '14px', fontWeight: 'bold' }}>Admin</h4>
                                        <p style={{ margin: 0, fontSize: '10px', color: '#666', lineHeight: '1.4' }}>
                                            Full access to manage devices, users and system.
                                        </p>
                                    </div>

                                    {/* Guest Card */}
                                    <div
                                        onClick={() => handleRoleSelect('Guest')}
                                        style={{
                                            flex: 1,
                                            border: newUser.role === 'Guest' ? '2px solid #536bf6' : '1px solid #e2e8f0',
                                            borderRadius: '16px',
                                            padding: newUser.role === 'Guest' ? '15px' : '16px', // Adjust padding to maintain size
                                            cursor: 'pointer',
                                            backgroundColor: newUser.role === 'Guest' ? '#eff6ff' : 'white', // Using light blue for selected guest too
                                            textAlign: 'center',
                                            transition: 'all 0.2s',
                                            boxSizing: 'border-box'
                                        }}
                                    >
                                        <div style={{
                                            backgroundColor: '#64748b', width: '40px', height: '40px', borderRadius: '10px',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 10px auto', color: 'white'
                                        }}>
                                            <UserX size={20} />
                                        </div>
                                        <h4 style={{ margin: '0 0 5px 0', fontSize: '14px', fontWeight: 'bold' }}>Guest</h4>
                                        <p style={{ margin: 0, fontSize: '10px', color: '#666', lineHeight: '1.4' }}>
                                            Limited access to view devices and monitor system status.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Buttons */}
                            <div style={{ display: 'flex', gap: '15px', marginTop: '10px' }}>
                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    style={{
                                        flex: 1, backgroundColor: '#536bf6', color: 'white', border: 'none',
                                        padding: '12px', borderRadius: '25px', cursor: isLoading ? 'not-allowed' : 'pointer',
                                        fontSize: '14px', fontWeight: '600', boxShadow: '0 4px 10px rgba(83, 107, 246, 0.3)'
                                    }}
                                >
                                    {isLoading ? 'Creating...' : 'Create Account'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    style={{
                                        flex: 1, backgroundColor: '#64748b', color: 'white', border: 'none',
                                        padding: '12px', borderRadius: '25px', cursor: 'pointer',
                                        fontSize: '14px', fontWeight: '600'
                                    }}
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MembersWidget;
