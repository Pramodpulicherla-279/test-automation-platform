import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Play, History, ChevronLeft, ChevronRight, LayoutDashboard, Zap, FileJson } from 'lucide-react';

const NAV_ITEMS = [
    {
        label: 'Run Tests',
        to: '/',
        icon: <Play size={20} />,
    },
    {
        label: 'API Tester',
        to: '/api-tester',
        icon: <Zap size={20} />,
   },
    {
        label: 'API Batch',
        to: '/api-batch',
        icon: <FileJson size={20} />,
    },
    {
        label: 'Jira History',
        to: '/jira-history',
        icon: <History size={20} />,
    },
];

export default function Sidebar() {
    const [collapsed, setCollapsed] = useState(false);

    return (
        <>
            <aside
                style={{
                    width: collapsed ? '64px' : '220px',
                    height: '100vh',
                    background: '#F8FAFC',
                    borderRight: '1px solid #CBD5E1',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'width 0.25s ease',
                    overflow: 'hidden',
                    flexShrink: 0,

                }}
            >
                {/* Logo / Brand */}
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '20px 16px 16px',
                        borderBottom: '1px solid #CBD5E1',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                    }}
                >
                    <LayoutDashboard size={22} color="#38bdf8" style={{ flexShrink: 0 }} />
                    {!collapsed && (
                        <span style={{ color: '#38bdf8', fontWeight: 700, fontSize: '15px', letterSpacing: '0.01em' }}>
                            TAP / Android
                            <p className="brand-subtitle">Test Automation Platform <br/> Live Profiler</p>

                        </span>
                    )}
                </div>

                {/* Nav Items */}
                <nav style={{ flex: 1, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {NAV_ITEMS.map(({ label, to, icon }) => (
                        <NavLink
                            key={to}
                            to={to}
                            style={({ isActive }) => ({
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px',
                                padding: '10px 12px',
                                borderRadius: '8px',
                                textDecoration: 'none',
                                color: isActive ? '#38bdf8' : '#94a3b8',
                                background: isActive ? '#1e3a5f' : 'transparent',
                                fontWeight: isActive ? 600 : 400,
                                fontSize: '14px',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                transition: 'background 0.15s, color 0.15s',
                            })}
                            onMouseEnter={e => {
                                if (!e.currentTarget.dataset.active) {
                                    e.currentTarget.style.background = '#1e293b';
                                    e.currentTarget.style.color = '#e2e8f0';
                                }
                            }}
                            onMouseLeave={e => {
                                if (!e.currentTarget.dataset.active) {
                                    e.currentTarget.style.background = '';
                                    e.currentTarget.style.color = '';
                                }
                            }}
                        >
                            <span style={{ flexShrink: 0 }}>{icon}</span>
                            {!collapsed && <span>{label}</span>}
                        </NavLink>
                    ))}
                </nav>

                {/* Collapse Toggle */}
                <button
                    onClick={() => setCollapsed(c => !c)}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: collapsed ? 'center' : 'flex-end',
                        gap: '6px',
                        padding: '12px 16px',
                        background: 'none',
                        border: 'none',
                        borderTop: '1px solid #CBD5E1',
                        color: '#64748b',
                        cursor: 'pointer',
                        fontSize: '13px',
                        whiteSpace: 'nowrap',
                    }}
                    title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                >
                    {collapsed ? <ChevronRight size={18} /> : (
                        <>
                            <span>Collapse</span>
                            <ChevronLeft size={18} />
                        </>
                    )}
                </button>
            </aside>
        </>
    );
}