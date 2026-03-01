import React, { useState, useEffect } from 'react';
import { ChevronRight, User, Shield } from 'lucide-react';
import { Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { fetchUsers } from '../services/api';
import '../App.css'; // Reuse global layout
import '../components/RightPanel.css'; // Reuse styles

const MembersPage = () => {
    const [members, setMembers] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadMembers = async () => {
        try {
            setLoading(true);
            const users = await fetchUsers();
            if (users) {
                // Add default status if missing
                const enrichedUsers = users.map(u => ({
                    ...u,
                    status: u.status || 'Active'
                }));
                setMembers(enrichedUsers);
            }
        } catch (error) {
            console.error("Failed to load members", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadMembers();
    }, []);



    // Pagination State
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 8;

    // User list (no filtering applied)
    const filteredMembers = members;

    // Pagination Logic
    const totalPages = Math.ceil(filteredMembers.length / itemsPerPage);
    const indexOfLastItem = currentPage * itemsPerPage;
    const indexOfFirstItem = indexOfLastItem - itemsPerPage;
    const currentItems = filteredMembers.slice(indexOfFirstItem, indexOfLastItem);

    // Change page
    const paginate = (pageNumber) => setCurrentPage(pageNumber);
    const nextPage = () => setCurrentPage(prev => Math.min(prev + 1, totalPages));
    const prevPage = () => setCurrentPage(prev => Math.max(prev - 1, 1));

    // Helper to render status style
    const renderStatus = (status) => {
        if (status === 'Active') return <span style={{
            backgroundColor: 'rgba(39, 174, 96, 0.15)',
            color: '#27ae60',
            padding: '4px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: '600',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px'
        }}><span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#27ae60' }}></span>Active</span>;

        if (status === 'Inactive') return <span style={{
            backgroundColor: 'rgba(255, 63, 52, 0.15)',
            color: '#ff3f34',
            padding: '4px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: '600',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px'
        }}><span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#ff3f34' }}></span>Inactive</span>;
        return status;
    };

    // Helper for Role Icon
    const getRoleIcon = (role) => {
        if (role === 'Administrator') return <Shield size={18} color="#536bf6" />;
        return <User size={18} color="#64748b" />;
    };

    return (
        <div className="app-container">
            <Sidebar />

            <div className="main-content" style={{ padding: '30px 40px', backgroundColor: '#f3f4f6' }}>
                {/* Breadcrumb */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '25px', fontSize: '14px', color: '#666' }}>
                    <Link to="/" style={{ textDecoration: 'none', color: '#666' }}>My Home</Link>
                    <ChevronRight size={16} />
                    <span style={{ color: '#222', fontWeight: '500' }}>Members</span>
                </div>

                {/* Main Card */}
                <div style={{ backgroundColor: 'white', borderRadius: '25px', padding: '30px 30px 20px 30px', boxShadow: '0 4px 20px rgba(0,0,0,0.03)', minHeight: '60vh', display: 'flex', flexDirection: 'column' }}>

                    {/* Header with Title */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px', marginTop: '-10px' }}>
                        <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#273c75', margin: 0 }}>All Members</h1>
                    </div>

                    {/* Table Header */}
                    <div style={{ display: 'flex', backgroundColor: '#f8f9fa', padding: '15px 20px', borderRadius: '10px', marginBottom: '10px' }}>
                        <div style={{ flex: 2, fontSize: '14px', fontWeight: '600', color: '#555' }}>Name</div>
                        <div style={{ flex: 2, fontSize: '14px', fontWeight: '600', color: '#555' }}>Email</div>
                        <div style={{ flex: 1.5, fontSize: '14px', fontWeight: '600', color: '#555' }}>Role</div>
                        <div style={{ flex: 1.5, fontSize: '14px', fontWeight: '600', color: '#555', textAlign: 'right' }}>Status</div>
                        <div style={{ width: '40px' }}></div>
                    </div>

                    {/* Members List */}
                    <div className="members-list-full" style={{ flex: 1 }}>
                        {loading ? (
                            <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>Loading members...</div>
                        ) : currentItems.length === 0 ? (
                            <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>No members found</div>
                        ) : (
                            currentItems.map((member, index) => (
                                <div key={index} style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    padding: '15px 20px',
                                    borderBottom: '1px solid #f0f0f0',
                                    transition: 'background-color 0.2s'
                                }}
                                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#fafafa'}
                                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                                >
                                    {/* Name & Avatar */}
                                    <div style={{ flex: 2, display: 'flex', alignItems: 'center', gap: '15px' }}>
                                        <div style={{
                                            width: '40px', height: '40px',
                                            borderRadius: '50%',
                                            backgroundColor: member.role === 'Administrator' ? '#eff6ff' : '#f1f5f9',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            color: member.role === 'Administrator' ? '#536bf6' : '#64748b'
                                        }}>
                                            <User size={20} />
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                                            <span style={{ fontWeight: '600', color: '#222', fontSize: '14px' }}>{member.full_name}</span>
                                        </div>
                                    </div>

                                    {/* Email */}
                                    <div style={{ flex: 2, color: '#555', fontSize: '14px' }}>
                                        {member.email}
                                    </div>

                                    {/* Role */}
                                    <div style={{ flex: 1.5, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        {getRoleIcon(member.role)}
                                        <span style={{ fontSize: '14px', color: '#444' }}>{member.role}</span>
                                    </div>

                                    {/* Status */}
                                    <div style={{ flex: 1.5, textAlign: 'right' }}>
                                        {renderStatus(member.status)}
                                    </div>


                                </div>
                            ))
                        )}
                    </div>

                    {/* Pagination Controls */}
                    {totalPages > 1 && (
                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: 'auto', paddingTop: '20px', gap: '10px' }}>
                            <button
                                onClick={prevPage}
                                disabled={currentPage === 1}
                                style={{
                                    padding: '8px 16px',
                                    borderRadius: '8px',
                                    border: '1px solid #e0e0e0',
                                    backgroundColor: currentPage === 1 ? '#f9fafb' : 'white',
                                    color: currentPage === 1 ? '#ccc' : '#444',
                                    cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                                    fontSize: '14px'
                                }}
                            >
                                Previous
                            </button>

                            {[...Array(totalPages)].map((_, i) => (
                                <button
                                    key={i}
                                    onClick={() => paginate(i + 1)}
                                    style={{
                                        width: '36px',
                                        height: '36px',
                                        borderRadius: '8px', // Square-ish with rounded corners
                                        border: currentPage === i + 1 ? 'none' : '1px solid #e0e0e0',
                                        backgroundColor: currentPage === i + 1 ? '#4361ee' : 'white',
                                        color: currentPage === i + 1 ? 'white' : '#444',
                                        cursor: 'pointer',
                                        fontWeight: '600',
                                        fontSize: '14px',
                                        transition: 'all 0.2s',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                    }}
                                >
                                    {i + 1}
                                </button>
                            ))}

                            <button
                                onClick={nextPage}
                                disabled={currentPage === totalPages}
                                style={{
                                    padding: '8px 16px',
                                    borderRadius: '8px',
                                    border: '1px solid #e0e0e0',
                                    backgroundColor: currentPage === totalPages ? '#f9fafb' : 'white',
                                    color: currentPage === totalPages ? '#ccc' : '#444',
                                    cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                                    fontSize: '14px'
                                }}
                            >
                                Next
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MembersPage;
