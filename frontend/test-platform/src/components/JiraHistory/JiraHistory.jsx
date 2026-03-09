import React, { useState, useEffect } from 'react';
import {
    History, ExternalLink, AlertCircle, CheckCircle,
    Clock, RefreshCw, Search, ChevronDown
} from 'lucide-react';
import Header from '../Header/Header';
import useWebSocket, { ReadyState } from 'react-use-websocket';


const WS_URL = 'ws://localhost:8000/ws/test-status';
const API_URL = 'http://localhost:8000';
// --- Sample data shown when API is unavailable ---
const SAMPLE_ISSUES = [
    { key: 'KV-101', summary: 'Login screen crashes on invalid OTP entry', status: 'Assigned', url: '#' },
    { key: 'KV-98', summary: 'Onboarding flow skips address step on Android 13', status: 'Assigned', url: '#' },
    { key: 'KV-95', summary: 'Marketplace images not loading on slow network', status: 'Unassigned', url: '#' },
    { key: 'KV-91', summary: 'Cart total mismatch after applying coupon code', status: 'Unassigned', url: '#' },
    { key: 'KV-87', summary: 'Farmer profile photo upload fails > 5MB', status: 'Assigned', url: '#' },
];

const STATUS_CONFIG = {
    'Assigned': { color: '#16a34a', bg: '#dcfce7', icon: <CheckCircle size={13} /> },
    'In Progress': { color: '#2563eb', bg: '#dbeafe', icon: <Clock size={13} /> },
    'Unassigned': { color: '#64748b', bg: '#f1f5f9', icon: <AlertCircle size={13} /> },
};

const PRIORITY_CONFIG = {
    'high': { color: '#dc2626' },
    'medium': { color: '#d97706' },
    'low': { color: '#64748b' },
};

const getStatus = (status = '') => STATUS_CONFIG[status.toLowerCase()] ?? STATUS_CONFIG['Unassigned'];
const getPriority = (priority = '') => PRIORITY_CONFIG[priority.toLowerCase()] ?? PRIORITY_CONFIG['low'];

export default function JiraHistory() {
    const [issues, setIssues] = useState(SAMPLE_ISSUES);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [search, setSearch] = useState('');
    const [appIcon, setAppIcon] = useState(null);
    const [appTitle, setAppTitle] = useState('');
    const [isDeviceConnected, setIsDeviceConnected] = useState(false);
    const [appiumStatus, setAppiumStatus] = useState('stopped');

    const [statusFilter, setStatusFilter] = useState('All');
    const { lastJsonMessage, sendMessage, readyState } = useWebSocket(WS_URL, {
        shouldReconnect: () => true,
        onMessage: (event) => {
            const data = JSON.parse(event.data);
            handleIncomingData(data);
        }
    });
    const fetchIssues = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_URL}/jira/history`);
            if (!res.ok) throw new Error(`Server error: ${res.status}`);
            const data = await res.json();
            setIssues(data.issues ?? data);
        } catch (err) {
            setError('Could not fetch from server — showing sample data.');
            setIssues(SAMPLE_ISSUES);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchIssues(); }, []);

    const filtered = issues.filter(issue => {
        const matchesSearch =
            !search ||
            issue.key.toLowerCase().includes(search.toLowerCase()) ||
            issue.summary.toLowerCase().includes(search.toLowerCase()) ||
            (issue.assignee ?? '').toLowerCase().includes(search.toLowerCase());
        const matchesStatus =
            statusFilter === 'All' || issue.status.toLowerCase() === statusFilter.toLowerCase();
        return matchesSearch && matchesStatus;
    });

    const statuses = ['All', ...Array.from(new Set(issues.map(i => i.status)))];

    return (
        <div style={{ padding: '12px' }}>

            {/* Page Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <History size={22} color="var(--accent-blue)" />
                    <div>
                        <h1 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                            Jira History
                        </h1>
                        {/* <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            Test-linked issues from your Jira project
                        </p> */}
                    </div>
                </div>

                <button
                    onClick={fetchIssues}
                    disabled={loading}
                    className="run-button"
                    style={{ backgroundColor: 'var(--bg-card)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', padding: '8px 14px' }}
                >
                    <RefreshCw size={14} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
                    Refresh
                </button>
            </div>

            {/* Error Banner */}
            {error && (
                <div style={{
                    display: 'flex', alignItems: 'center', gap: '8px',
                    background: '#fef9c3', border: '1px solid #fde047',
                    borderRadius: '8px', padding: '10px 16px',
                    color: '#854d0e', fontSize: '0.875rem', marginBottom: '20px'
                }}>
                    <AlertCircle size={16} /> {error}
                </div>
            )}

            {/* Summary Cards */}
            <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
                {[
                    { label: 'Total Issues', value: issues.length, color: 'var(--accent-blue)' },
                    { label: 'Assigned', value: issues.filter(i => i.status.toLowerCase() === 'in progress').length, color: '#d97706' },
                    { label: 'Unassigned', value: issues.filter(i => i.status.toLowerCase() === 'done').length, color: '#16a34a' },
                ].map(({ label, value, color }) => (
                    <div key={label} className="dashboard-card" style={{ flex: '1', minWidth: '120px', padding: '16px', height: 'auto' }}>
                        <div style={{ fontSize: '1.75rem', fontWeight: 700, color }}>{value}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{label}</div>
                    </div>
                ))}
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
                {/* Search */}
                <div style={{ position: 'relative', flex: '1', minWidth: '200px' }}>
                    <Search size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                    <input
                        type="text"
                        placeholder="Search by key, summary, assignee..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="text-input"
                        style={{ paddingLeft: '36px', width: '100%', boxSizing: 'border-box' }}
                    />
                </div>

                {/* Status Filter */}
                <div style={{ display: 'flex', gap: '6px' }}>
                    {statuses.map(s => (
                        <button
                            key={s}
                            onClick={() => setStatusFilter(s)}
                            style={{
                                padding: '6px 14px',
                                borderRadius: '999px',
                                border: '1px solid var(--border-color)',
                                cursor: 'pointer',
                                fontSize: '0.8rem',
                                fontWeight: statusFilter === s ? 600 : 400,
                                background: statusFilter === s ? 'var(--accent-blue)' : 'var(--bg-card)',
                                color: statusFilter === s ? '#fff' : 'var(--text-secondary)',
                                transition: 'all 0.15s',
                            }}
                        >
                            {s}
                        </button>
                    ))}
                </div>
            </div>

            {/* Table */}
            <div className="dashboard-card" style={{ padding: 0, height: 'auto', overflow: 'hidden' }}>
                {loading ? (
                    <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-secondary)' }}>
                        <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }} />
                        <div>Loading issues…</div>
                    </div>
                ) : filtered.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-secondary)' }}>
                        No issues match your filters.
                    </div>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                            <thead>
                                <tr style={{ background: '#F8FAFC', borderBottom: '1px solid var(--border-color)' }}>
                                    {['Key', 'Summary', 'Status'].map(h => (
                                        <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                                            {h}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.map((issue, i) => {
                                    const { color: sColor, bg: sBg, icon: sIcon } = getStatus(issue.status);
                                    const { color: pColor } = getPriority(issue.priority);
                                    return (
                                        <tr
                                            key={issue.key ?? i}
                                            style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.1s' }}
                                            onMouseEnter={e => e.currentTarget.style.background = '#F8FAFC'}
                                            onMouseLeave={e => e.currentTarget.style.background = ''}
                                        >
                                            <td style={{ padding: '12px 16px', fontWeight: 600 }}>
                                                {issue.url && issue.url !== '#' ? (
                                                    <a
                                                        href={issue.url}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        style={{ color: 'var(--accent-blue)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                                                    >
                                                        {issue.key} <ExternalLink size={12} />
                                                    </a>
                                                ) : (
                                                    <span style={{ color: 'var(--accent-blue)' }}>{issue.key}</span>
                                                )}
                                            </td>
                                            <td style={{ padding: '12px 16px', color: 'var(--text-primary)', maxWidth: '320px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                {issue.summary}
                                            </td>
                                            <td style={{ padding: '12px 16px' }}>
                                                <span style={{
                                                    display: 'inline-flex', alignItems: 'center', gap: '5px',
                                                    color: sColor, background: sBg,
                                                    padding: '3px 10px', borderRadius: '999px',
                                                    fontSize: '0.75rem', fontWeight: 600
                                                }}>
                                                    {sIcon} {issue.status}
                                                </span>
                                            </td>
                                            {/* <td style={{ padding: '12px 16px' }}>
                                                <span style={{ color: pColor, fontWeight: 600, fontSize: '0.8rem' }}>
                                                    {issue.priority ?? '—'}
                                                </span>
                                            </td> */}
                                            {/* <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                                                {issue.assignee ?? 'Unassigned'}
                                            </td>
                                            <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>
                                                {issue.updated ? new Date(issue.updated).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}
                                            </td> */}
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            <p style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                {filtered.length} of {issues.length} issues shown
            </p>
        </div>
    );
}