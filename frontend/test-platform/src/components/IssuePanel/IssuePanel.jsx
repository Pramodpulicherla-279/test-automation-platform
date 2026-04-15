import React, { useState } from "react";
import { AlertCircle, ChevronDown, ChevronRight, Maximize2, Minimize2, Plus, Trash2 } from 'lucide-react';

const DEVELOPERS = ['Unassigned', 'Anuj', 'Vaibhav', 'Vikash', 'Swaroopa'];
const PRIORITIES = ['High', 'Medium', 'Low'];
const PRIORITY_COLOR = { High: '#dc2626', Medium: '#d97706', Low: '#64748b' };

const emptyIssue = () => ({
    issueId: '', title: '', description: '',
    developer: 'Unassigned', priority: 'Medium',
    parent: '', fixVersion: '', testId: ''
});

const IssuePanel = ({ modules }) => {
    const [issues, setIssues] = useState([]);
    const [expandedIdx, setExpandedIdx] = useState(null);
    const [isFullScreen, setIsFullScreen] = useState(false);

    const toggleAccordion = (idx) => setExpandedIdx(prev => prev === idx ? null : idx);

    const addNew = () => {
        setIssues(prev => [...prev, emptyIssue()]);
        setExpandedIdx(issues.length);
    };

    const updateField = (idx, field, value) =>
        setIssues(prev => prev.map((iss, i) => i === idx ? { ...iss, [field]: value } : iss));

    const deleteIssue = (idx) => {
        setIssues(prev => prev.filter((_, i) => i !== idx));
        setExpandedIdx(prev => prev === idx ? null : prev > idx ? prev - 1 : prev);
    };

    const labelStyle = { fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px', display: 'block' };
    const inputStyle = { width: '100%', boxSizing: 'border-box', background: 'var(--input-bg)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '7px 10px', fontSize: '0.8rem', color: 'var(--text-primary)' };

    return (
        <div style={{
            display: 'flex', flexDirection: 'column',
            height: isFullScreen ? '100vh' : '350px',
            ...(isFullScreen ? { position: 'fixed', top: 0, left: 0, width: '100vw', zIndex: 9999, borderRadius: 0 }
                : { borderRadius: '0.75rem' }),
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            overflow: 'auto',
            fontFamily: "'Courier New', Courier, monospace",
            boxShadow: '0px 2px 4px rgba(15,23,42,0.04), 0px 8px 24px rgba(15,23,42,0.08)',
        }}>
            {/* Header */}
            <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '0.8rem', borderBottom: '1px solid var(--border-color)',
                background: 'var(--bg-console)', flexShrink: 0,
                position: 'sticky', top: 0, zIndex: 10,
            }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
                    <AlertCircle size={14} color="var(--accent-blue)" /> ISSUE LIST
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', background: 'var(--border-color)', borderRadius: '999px', padding: '2px 8px' }}>
                        {issues.length} issue{issues.length !== 1 ? 's' : ''}
                    </span>
                    <button
                        onClick={addNew}
                        style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--accent-blue)', border: 'none', borderRadius: '6px', padding: '4px 10px', cursor: 'pointer', fontSize: '0.72rem', color: '#fff', fontWeight: 600 }}
                        title="New Issue"
                    >
                        <Plus size={13} /> New
                    </button>
                    <button
                        onClick={() => setIsFullScreen(f => !f)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', display: 'flex', alignItems: 'center', padding: '4px' }}
                        title={isFullScreen ? 'Exit Full Screen' : 'Full Screen'}
                    >
                        {isFullScreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                    </button>
                </div>
            </div>

            {/* Accordion list */}
            <div style={{ flex: 1, minHeight: 500,overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {issues.length === 0 && (
                    <div style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8rem', padding: '32px 16px' }}>
                        No issues yet. Click <strong>+ New</strong> to add one.
                    </div>
                )}
                {issues.map((iss, idx) => {
                    const isOpen = expandedIdx === idx;
                    const pColor = PRIORITY_COLOR[iss.priority] ?? '#64748b';
                    return (
                        <div key={idx} style={{ border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden', background: 'var(--bg-card)' }}>
                            {/* Accordion Header */}
                            <button
                                onClick={() => toggleAccordion(idx)}
                                style={{
                                    width: '100%', display: 'flex', alignItems: 'center', gap: '8px',
                                    padding: '8px 10px', background: isOpen ? 'var(--input-bg)' : 'transparent',
                                    border: 'none', cursor: 'pointer', textAlign: 'left',
                                    borderBottom: isOpen ? '1px solid var(--border-color)' : 'none',
                                    transition: 'background 0.15s',
                                }}
                            >
                                {isOpen ? <ChevronDown size={14} color="var(--text-secondary)" /> : <ChevronRight size={14} color="var(--text-secondary)" />}
                                <span style={{ color: 'var(--accent-blue)', fontWeight: 700, fontSize: '0.8rem', flexShrink: 0 }}>
                                    {iss.issueId || `#${idx + 1}`}
                                </span>
                                <span style={{ flex: 1, fontSize: '0.8rem', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {iss.title || <em style={{ color: 'var(--text-secondary)' }}>Untitled</em>}
                                </span>
                                <span style={{ color: pColor, fontSize: '0.72rem', fontWeight: 600, flexShrink: 0, marginLeft: '4px' }}>
                                    {iss.priority}
                                </span>
                            </button>

                            {/* Accordion Body — inline editable fields */}
                            {isOpen && (
                                <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    {/* Test ID */}
                                    <div>
                                        <label style={labelStyle}>Test ID</label>
                                        <select style={inputStyle} value={iss.testId} onChange={e => updateField(idx, 'testId', e.target.value)}>
                                            <option value="">-- Select Test --</option>
                                            {modules.map((m, i) => (
                                                <option key={i} value={m.name}>{m.name} ({m.status})</option>
                                            ))}
                                        </select>
                                    </div>

                                    {/* Issue ID + Title */}
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <div style={{ flex: '0 0 36%' }}>
                                            <label style={labelStyle}>Issue ID</label>
                                            <input style={inputStyle} placeholder="KV-102" value={iss.issueId} onChange={e => updateField(idx, 'issueId', e.target.value)} />
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <label style={labelStyle}>Title <span style={{ color: '#ef4444' }}>*</span></label>
                                            <input style={inputStyle} placeholder="Issue title..." value={iss.title} onChange={e => updateField(idx, 'title', e.target.value)} />
                                        </div>
                                    </div>

                                    {/* Description */}
                                    <div>
                                        <label style={labelStyle}>Description</label>
                                        <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: '56px' }} placeholder="Describe the issue..." value={iss.description} onChange={e => updateField(idx, 'description', e.target.value)} />
                                    </div>

                                    {/* Developer + Priority */}
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <div style={{ flex: 1 }}>
                                            <label style={labelStyle}>Developer</label>
                                            <select style={inputStyle} value={iss.developer} onChange={e => updateField(idx, 'developer', e.target.value)}>
                                                {DEVELOPERS.map(d => <option key={d}>{d}</option>)}
                                            </select>
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <label style={labelStyle}>Priority</label>
                                            <select style={inputStyle} value={iss.priority} onChange={e => updateField(idx, 'priority', e.target.value)}>
                                                {PRIORITIES.map(p => <option key={p}>{p}</option>)}
                                            </select>
                                        </div>
                                    </div>

                                    {/* Parent + Fix Version */}
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <div style={{ flex: 1 }}>
                                            <label style={labelStyle}>Parent</label>
                                            <input style={inputStyle} placeholder="KV-90" value={iss.parent} onChange={e => updateField(idx, 'parent', e.target.value)} />
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <label style={labelStyle}>Fix Version</label>
                                            <input style={inputStyle} placeholder="v2.1.0" value={iss.fixVersion} onChange={e => updateField(idx, 'fixVersion', e.target.value)} />
                                        </div>
                                    </div>

                                    {/* Delete */}
                                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2px' }}>
                                        <button
                                            onClick={() => deleteIssue(idx)}
                                            style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'none', border: '1px solid #dc2626', borderRadius: '4px', padding: '3px 10px', cursor: 'pointer', fontSize: '0.75rem', color: '#dc2626' }}
                                        >
                                            <Trash2 size={11} /> Delete
                                        </button>
                                        <button
                                            onClick={() => { if (iss.title.trim()) setExpandedIdx(null); }}
                                            className="run-button"
                                            style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px 14px', margin: '0 0 0 12px', fontSize: '0.78rem' }}
                                            title={!iss.title.trim() ? 'Title is required' : ''}
                                        >
                                            <Plus size={13} /> {idx === issues.length - 1 && !iss.issueId ? 'Create Issue' : 'Save'}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default IssuePanel;