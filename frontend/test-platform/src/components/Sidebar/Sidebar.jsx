import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Play, History, ChevronLeft, ChevronRight, LayoutDashboard, Zap, FileJson } from 'lucide-react';

const NAV_ITEMS = [
    { label: 'Run Tests',    to: '/',            icon: <Play size={18} /> },
    { label: 'API Matrix',   to: '/api-matrix',  icon: <Zap size={18} /> },
    { label: 'API Batch',    to: '/api-batch',   icon: <FileJson size={18} /> },
    { label: 'Jira History', to: '/jira-history',icon: <History size={18} /> },
];

export default function Sidebar() {
    const [collapsed, setCollapsed] = useState(false);

    return (
        <aside style={{
            width: collapsed ? '60px' : '210px',
            height: '100vh',
            background: '#FFFFFF',
            borderRight: '1px solid #E2E8F0',
            display: 'flex',
            flexDirection: 'column',
            transition: 'width 0.22s ease',
            overflow: 'hidden',
            flexShrink: 0,
            boxShadow: '1px 0 4px rgba(15,23,42,0.04)',
        }}>

            {/* ── Brand ── */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: collapsed ? '18px 0' : '18px 16px 16px',
                borderBottom: '1px solid #E2E8F0',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                justifyContent: collapsed ? 'center' : 'flex-start',
            }}>
                <div style={{
                    width: '32px', height: '32px',
                    background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
                    borderRadius: '8px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0,
                    boxShadow: '0 2px 6px rgba(37,99,235,0.3)',
                }}>
                    <LayoutDashboard size={17} color="#fff" />
                </div>
                {!collapsed && (
                    <div>
                        <div style={{
                            color: '#0F172A',
                            fontWeight: 800,
                            fontSize: '13.5px',
                            letterSpacing: '-0.01em',
                            lineHeight: '1.2',
                        }}>
                            TAP / Android
                        </div>
                        <div style={{
                            color: '#94A3B8',
                            fontSize: '10px',
                            marginTop: '2px',
                            lineHeight: '1.35',
                        }}>
                            Test Automation Platform
                        </div>
                    </div>
                )}
            </div>

            {/* ── Nav Items ── */}
            <nav style={{ flex: 1, padding: '10px 8px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {NAV_ITEMS.map(({ label, to, icon }) => (
                    <NavLink
                        key={to}
                        to={to}
                        title={collapsed ? label : undefined}
                        style={({ isActive }) => ({
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            padding: collapsed ? '10px 0' : '9px 12px',
                            justifyContent: collapsed ? 'center' : 'flex-start',
                            borderRadius: '8px',
                            textDecoration: 'none',
                            color: isActive ? '#2563EB' : '#64748B',
                            background: isActive ? '#EFF6FF' : 'transparent',
                            fontWeight: isActive ? 700 : 500,
                            fontSize: '13px',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            transition: 'background 0.15s, color 0.15s',
                            borderLeft: isActive ? '3px solid #2563EB' : '3px solid transparent',
                        })}
                        onMouseEnter={e => {
                            // Only style non-active items on hover
                            if (e.currentTarget.style.background !== 'rgb(239, 246, 255)') {
                                e.currentTarget.style.background = '#F8FAFC';
                                e.currentTarget.style.color = '#0F172A';
                            }
                        }}
                        onMouseLeave={e => {
                            if (e.currentTarget.style.background !== 'rgb(239, 246, 255)') {
                                e.currentTarget.style.background = 'transparent';
                                e.currentTarget.style.color = '#64748B';
                            }
                        }}
                    >
                        <span style={{ flexShrink: 0 }}>{icon}</span>
                        {!collapsed && <span>{label}</span>}
                    </NavLink>
                ))}
            </nav>

            {/* ── Collapse Toggle ── */}
            <button
                onClick={() => setCollapsed(c => !c)}
                title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: collapsed ? 'center' : 'flex-end',
                    gap: '6px',
                    padding: '12px 16px',
                    background: 'none',
                    border: 'none',
                    borderTop: '1px solid #E2E8F0',
                    color: '#94A3B8',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontFamily: 'inherit',
                    whiteSpace: 'nowrap',
                    transition: 'color 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.color = '#475569'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#94A3B8'; }}
            >
                {collapsed ? <ChevronRight size={16} /> : (
                    <>
                        <span style={{ fontSize: '12px', fontWeight: 500 }}>Collapse</span>
                        <ChevronLeft size={16} />
                    </>
                )}
            </button>
        </aside>
    );
}
