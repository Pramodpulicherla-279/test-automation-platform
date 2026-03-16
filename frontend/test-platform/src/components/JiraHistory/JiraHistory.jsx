/**
 * JiraHistory.jsx
 *
 * Changes:
 *  - Receives history from IssuePanel via issuePanelHistory prop
 *  - Tabs: All | Assigned (created tickets) | Unassigned (removed tickets)
 *  - Summary cards show Total / Assigned / Unassigned counts
 *  - Assigned list: shows Jira key + link
 *  - Unassigned list: shows removed issues without Jira key
 */

import React, { useState, useEffect } from 'react';
import { History, ExternalLink, CheckCircle, AlertCircle, Clock, RefreshCw, Search } from 'lucide-react';

const API_URL = 'http://localhost:8000';

const STATUS_CONFIG = {
  Assigned:   { color: '#16a34a', bg: '#dcfce7', icon: <CheckCircle size={13} /> },
  Unassigned: { color: '#64748b', bg: '#f1f5f9', icon: <AlertCircle  size={13} /> },
  'In Progress': { color: '#2563eb', bg: '#dbeafe', icon: <Clock size={13} /> },
};
const getStatus = (s = '') => STATUS_CONFIG[s] ?? STATUS_CONFIG['Unassigned'];

const PillBtn = ({ active, onClick, children }) => (
  <button onClick={onClick} style={{
    padding: '6px 16px', borderRadius: '999px', border: '1px solid var(--border-color)',
    cursor: 'pointer', fontSize: '0.8rem', fontWeight: active ? 700 : 400,
    background: active ? 'var(--accent-blue)' : 'var(--bg-card)',
    color: active ? '#fff' : 'var(--text-secondary)', transition: 'all 0.15s',
  }}>
    {children}
  </button>
);

/* ────────────────────────────────────────────────────────────────────────────
 * Props:
 *   issuePanelHistory  – array of { type: 'created'|'removed', issueId,
 *                                   title, jiraUrl, module, priority,
 *                                   developer, savedAt, ... }
 *                        Pushed by IssuePanel via onHistoryUpdate callback.
 * ────────────────────────────────────────────────────────────────────────── */
export default function JiraHistory({ issuePanelHistory = [] }) {
  const [apiIssues,     setApiIssues]     = useState([]);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState(null);
  const [search,        setSearch]        = useState('');
  const [activeTab,     setActiveTab]     = useState('all');  // 'all' | 'assigned' | 'unassigned'

  // Fetch from /api/jira/history on mount + refresh
  const fetchIssues = async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${API_URL}/api/jira/history`);
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setApiIssues(data.issues ?? []);
    } catch {
      // Try legacy endpoint
      try {
        const res2 = await fetch(`${API_URL}/jira/history`);
        if (res2.ok) {
          const data2 = await res2.json();
          setApiIssues(data2.issues ?? []);
          return;
        }
      } catch {}
      setError('Could not fetch from server');
      setApiIssues([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchIssues(); }, []);

  // Merge: API history (created this session) + IssuePanel prop history
  // IssuePanel prop history is the live session data (created + removed)
  const panelCreated  = issuePanelHistory.filter(h => h.type === 'created');
  const panelRemoved  = issuePanelHistory.filter(h => h.type === 'removed');

  // Deduplicate: prefer panelCreated over apiIssues (panelCreated is real-time)
  const panelCreatedKeys = new Set(panelCreated.map(h => h.issueId).filter(Boolean));
  const apiOnly = apiIssues.filter(i => !panelCreatedKeys.has(i.issue_id || i.key));

  // All assigned = API history + real-time created
  const allAssigned = [
    ...panelCreated.map(h => ({
      key:      h.issueId      || '—',
      summary:  h.title        || 'Untitled',
      status:   'Assigned',
      url:      h.jiraUrl      || '',
      priority: h.priority     || 'High',
      assignee: h.developer    || '',
      module:   h.module       || '',
      savedAt:  h.savedAt      || '',
    })),
    ...apiOnly.map(i => ({
      key:      i.issue_id || i.key || '—',
      summary:  i.title    || i.summary || 'Untitled',
      status:   i.status   || 'Assigned',
      url:      i.issue_url || i.url || '',
      priority: i.priority || 'High',
      assignee: i.developer_name || i.assignee || '',
      module:   i.module   || '',
      savedAt:  i.created_at || i.updated || '',
    })),
  ];

  // All unassigned = removed from IssuePanel
  const allUnassigned = panelRemoved.map(h => ({
    key:      h.internal_issue_id ? `#${h.internal_issue_id}` : '—',
    summary:  h.title     || 'Untitled',
    status:   'Unassigned',
    url:      '',
    priority: h.priority  || 'Medium',
    assignee: h.developer || '',
    module:   h.module    || '',
    savedAt:  h.savedAt   || '',
  }));

  // Filtered lists
  const filterFn = (rows) => rows.filter(row => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      row.key.toLowerCase().includes(q) ||
      row.summary.toLowerCase().includes(q) ||
      (row.assignee || '').toLowerCase().includes(q) ||
      (row.module   || '').toLowerCase().includes(q)
    );
  });

  const shownRows = activeTab === 'assigned'
    ? filterFn(allAssigned)
    : activeTab === 'unassigned'
    ? filterFn(allUnassigned)
    : filterFn([...allAssigned, ...allUnassigned]);

  const total      = allAssigned.length + allUnassigned.length;
  const assignedCt = allAssigned.length;
  const unassignedCt = allUnassigned.length;

  /* ── Summary card ── */
  const SummaryCard = ({ label, value, color }) => (
    <div className="dashboard-card" style={{ flex: 1, minWidth: 160 }}>
      <div style={{ fontSize: '2rem', fontWeight: 800, color }}>{value}</div>
      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 4 }}>{label}</div>
    </div>
  );

  /* ── Table row ── */
  const TableRow = ({ row }) => {
    const st = getStatus(row.status);
    return (
      <tr style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.1s' }}
        onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-console)'}
        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
        <td style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--accent-blue)', whiteSpace: 'nowrap' }}>
          {row.url
            ? <a href={row.url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-blue)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                {row.key} <ExternalLink size={11} />
              </a>
            : <span style={{ color: 'var(--text-secondary)' }}>{row.key}</span>
          }
        </td>
        <td style={{ padding: '12px 16px', color: 'var(--text-primary)' }}>{row.summary}</td>
        {row.module && <td style={{ padding: '12px 16px' }}>
          <span style={{ background: '#ede9fe', color: '#7c3aed', borderRadius: 4, padding: '2px 8px', fontSize: '0.75rem', fontWeight: 700 }}>{row.module}</span>
        </td>}
        {!row.module && <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>—</td>}
        <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{row.assignee || '—'}</td>
        <td style={{ padding: '12px 16px' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: st.bg, color: st.color, borderRadius: 6, padding: '3px 10px', fontSize: '0.75rem', fontWeight: 700 }}>
            {st.icon} {row.status}
          </span>
        </td>
        <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontSize: '0.78rem', whiteSpace: 'nowrap' }}>
          {row.savedAt ? new Date(row.savedAt).toLocaleString() : '—'}
        </td>
      </tr>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

      {/* Page header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <History size={22} color="var(--accent-blue)" />
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>Jira History</h1>
        </div>
        <button onClick={fetchIssues} disabled={loading} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'var(--accent-blue)', color: '#fff', border: 'none',
          borderRadius: 8, padding: '8px 16px', cursor: 'pointer', fontSize: '0.875rem', fontWeight: 600,
        }}>
          <RefreshCw size={14} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <SummaryCard label="Total Issues"  value={total}        color="var(--accent-blue)" />
        <SummaryCard label="Assigned"      value={assignedCt}   color="#d97706" />
        <SummaryCard label="Unassigned"    value={unassignedCt} color="#64748b" />
      </div>

      {/* Search + Tabs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, position: 'relative', minWidth: 200 }}>
          <Search size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by key, summary, assignee…"
            style={{ width: '100%', boxSizing: 'border-box', paddingLeft: 36, paddingRight: 12, paddingTop: 10, paddingBottom: 10, borderRadius: 8, border: '1px solid var(--border-color)', background: 'var(--bg-card)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
          />
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <PillBtn active={activeTab === 'all'}        onClick={() => setActiveTab('all')}>
            All ({total})
          </PillBtn>
          <PillBtn active={activeTab === 'assigned'}   onClick={() => setActiveTab('assigned')}>
            Assigned ({assignedCt})
          </PillBtn>
          <PillBtn active={activeTab === 'unassigned'} onClick={() => setActiveTab('unassigned')}>
            Unassigned ({unassignedCt})
          </PillBtn>
        </div>
      </div>

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '10px 14px', color: '#b91c1c', fontSize: '0.85rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Table */}
      <div className="dashboard-card" style={{ padding: 0, overflow: 'hidden' }}>
        {shownRows.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-secondary)' }}>
            {loading ? 'Loading…' : activeTab === 'assigned' ? 'No assigned issues yet. Create tickets from the Issue Panel.' : activeTab === 'unassigned' ? 'No unassigned issues yet. Remove tickets from the Issue Panel.' : 'No issues yet.'}
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ background: 'var(--bg-console)', borderBottom: '1px solid var(--border-color)' }}>
                  {['Key', 'Summary', 'Module', 'Developer', 'Status', 'Date'].map(h => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {shownRows.map((row, i) => <TableRow key={i} row={row} />)}
              </tbody>
            </table>
            <div style={{ padding: '10px 16px', color: 'var(--text-secondary)', fontSize: '0.8rem', borderTop: '1px solid var(--border-color)' }}>
              {shownRows.length} of {activeTab === 'assigned' ? assignedCt : activeTab === 'unassigned' ? unassignedCt : total} issues shown
            </div>
          </div>
        )}
      </div>
    </div>
  );
}