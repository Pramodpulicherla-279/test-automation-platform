import React, { useEffect, useRef, useState } from "react";
import { AlertCircle, ChevronDown, ChevronRight, Maximize2, Minimize2, Plus, Trash2 } from 'lucide-react';

const DEVELOPERS = ['Unassigned', 'Anuj', 'Vaibhav', 'Vikash', 'Swaroopa'];
const PRIORITIES = ['High', 'Medium', 'Low'];
const PRIORITY_COLOR = { High: '#dc2626', Medium: '#d97706', Low: '#64748b' };

const emptyIssue = () => ({
  source: 'manual',       // 'manual' | 'draft'
  jiraUrl: '',
  issueId: '',            // filled after creation
  title: '',
  description: '',
  developer: 'Unassigned',
  priority: 'Medium',
  parent: '',
  fixVersion: '',
  testId: '',
  isEditing: true,        // manual starts editable
  rawPayload: null,       // original payload for Create
});

export default function IssuePanel({ modules, jiraIssues = [], apiUrl = 'http://localhost:8000' }) {
  const [issues, setIssues] = useState([]);
  const [expandedIdx, setExpandedIdx] = useState(null);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const importedKeysRef = useRef(new Set());

  const labelStyle = { fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px', display: 'block' };
  const inputStyle = { width: '100%', boxSizing: 'border-box', background: 'var(--input-bg)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '7px 10px', fontSize: '0.8rem', color: 'var(--text-primary)' };

  const safeString = (v) => (v === null || v === undefined ? '' : String(v));
  const pickFirst = (obj, keys) => {
    for (const k of keys) {
      const val = obj?.[k];
      if (val === null || val === undefined) continue;
      const s = String(val).trim();
      if (s) return val;
    }
    return '';
  };

  const getIssueKey = (payload) =>
    pickFirst(payload, ['issue_id', 'issueId', 'issue_key', 'issueKey', 'key', 'id']);

  const getFixVersionText = (payload) => {
    const v = payload?.fix_version ?? payload?.fixVersion ?? [];
    if (Array.isArray(v)) return v.filter(Boolean).map(String).join(', ');
    return safeString(v);
  };

  const mapPayloadToIssue = (payload) => {
    const issueKey = safeString(getIssueKey(payload));
    const title = safeString(pickFirst(payload, ['title', 'summary', 'issue_summary']));
    const description = safeString(pickFirst(payload, ['description']));
    const developer = safeString(pickFirst(payload, ['developer_name', 'developerName'])) || 'Unassigned';
    const moduleName = safeString(pickFirst(payload, ['module']));
    const parent = safeString(pickFirst(payload, ['parent'])) || moduleName;
    const fixVersion = safeString(getFixVersionText(payload));
    const jiraUrl = safeString(pickFirst(payload, ['issue_url', 'browse_url', 'url']));

    // Keep your existing mapping: testId dropdown uses module name
    const testId =
      moduleName && (modules || []).some(m => (m?.name || '').toLowerCase() === moduleName.toLowerCase())
        ? moduleName
        : '';

    const alreadyCreated = !!issueKey;

    return {
      ...emptyIssue(),
      source: 'draft',
      issueId: issueKey,         // may be empty for drafts; filled after Create
      jiraUrl,
      title,
      description,
      developer,
      parent,
      fixVersion,
      testId,
      isEditing: !alreadyCreated,  // drafts editable; created = read-only by default
      rawPayload: payload,
    };
  };

  // Import incoming jiraIssues into the accordion list only (no duplicate list view)
  useEffect(() => {
    const list = Array.isArray(jiraIssues) ? jiraIssues : [];
    if (!list.length) return;

    setIssues(prev => {
      const next = Array.isArray(prev) ? [...prev] : [];
      let lastInserted = -1;

      for (const payload of list) {
        const key = safeString(getIssueKey(payload) || JSON.stringify(payload));
        if (!key) continue;
        if (importedKeysRef.current.has(key)) continue;
        importedKeysRef.current.add(key);

        // Avoid duplicates if user already has the same issueId
        const issueId = safeString(getIssueKey(payload));
        if (issueId && next.some(x => safeString(x.issueId).trim() === issueId.trim())) continue;

        next.push(mapPayloadToIssue(payload));
        lastInserted = next.length - 1;
      }

      if (lastInserted >= 0) setExpandedIdx(lastInserted);
      return next;
    });
  }, [jiraIssues, modules]);

  const toggleAccordion = (idx) => setExpandedIdx(prev => (prev === idx ? null : idx));

  const addNew = () => {
    setIssues(prev => [...prev, emptyIssue()]);
    setExpandedIdx(issues.length);
  };

  const updateField = (idx, field, value) =>
    setIssues(prev => prev.map((iss, i) => (i === idx ? { ...iss, [field]: value } : iss)));

  const createIssue = (idx) => {
    setIssues(prev => prev.filter((_, i) => i !== idx));
    setExpandedIdx(prev => (prev === idx ? null : prev > idx ? prev - 1 : prev));
  };

  const toggleEdit = (idx) => {
    setIssues(prev => prev.map((iss, i) => (i === idx ? { ...iss, isEditing: !iss.isEditing } : iss)));
  };

  const createJira = async (idx) => {
    const iss = issues[idx];
    if (!iss) return;

    // You verify first, then click Create
    try {
      const payload = {
        ...(iss.rawPayload || {}),
        title: iss.title,
        description: iss.description,
        developer_name: iss.developer,
        parent: iss.parent,
        fix_version: iss.fixVersion ? [iss.fixVersion] : undefined,
        test_id: iss.testId || (iss.rawPayload?.test_id ?? ''),
      };

      const res = await fetch(`${apiUrl}/api/jira/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || 'Failed to create Jira issue');

      setIssues(prev => prev.map((x, i) => {
        if (i !== idx) return x;
        return {
          ...x,
          issueId: data.issue_id || data.issue_key || x.issueId,
          jiraUrl: data.issue_url || x.jiraUrl,
          isEditing: false,
        };
      }));
    } catch (e) {
      alert(e?.message || 'Failed to create Jira issue');
    }
  };

  const manualCount = issues.filter(i => i?.source === 'manual').length;
  const draftCount = issues.filter(i => i?.source === 'draft').length;

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
            {issues.length} total
          </span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', background: 'var(--border-color)', borderRadius: '999px', padding: '2px 8px' }}>
            {draftCount} jira
          </span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', background: 'var(--border-color)', borderRadius: '999px', padding: '2px 8px' }}>
            {manualCount} manual
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

      {/* Accordion list (single source of truth) */}
      <div style={{ flex: 1, minHeight: 500, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {issues.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8rem', padding: '32px 16px' }}>
            No issues yet. Click <strong>+ New</strong> to add one.
          </div>
        )}

        {issues.map((iss, idx) => {
          const isOpen = expandedIdx === idx;
          const pColor = PRIORITY_COLOR[iss.priority] ?? '#64748b';
          const readOnly = iss.source === 'draft' && !iss.isEditing;

          return (
            <div key={idx} style={{ border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden', background: 'var(--bg-card)' }}>
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

                <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--text-secondary)', background: 'var(--border-color)', borderRadius: '999px', padding: '2px 8px' }}>
                  {iss.source === 'draft' ? 'JIRA' : 'MANUAL'}
                </span>

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

              {isOpen && (
                <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div>
                    <label style={labelStyle}>Test ID</label>
                    <select style={inputStyle} value={iss.testId} disabled={readOnly} onChange={e => updateField(idx, 'testId', e.target.value)}>
                      <option value="">-- Select Test --</option>
                      {modules.map((m, i) => (
                        <option key={i} value={m.name}>{m.name} ({m.status})</option>
                      ))}
                    </select>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <div style={{ flex: '0 0 36%' }}>
                      <label style={labelStyle}>Issue ID</label>
                      <input style={inputStyle} placeholder="AT-123" value={iss.issueId} readOnly />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={labelStyle}>Title <span style={{ color: '#ef4444' }}>*</span></label>
                      <input style={inputStyle} placeholder="Issue title..." value={iss.title} disabled={readOnly} onChange={e => updateField(idx, 'title', e.target.value)} />
                    </div>
                  </div>

                  <div>
                    <label style={labelStyle}>Description</label>
                    <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: '56px' }} value={iss.description} disabled={readOnly} onChange={e => updateField(idx, 'description', e.target.value)} />
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <div style={{ flex: 1 }}>
                      <label style={labelStyle}>Developer</label>
                      <select style={inputStyle} value={iss.developer} disabled={readOnly} onChange={e => updateField(idx, 'developer', e.target.value)}>
                        {DEVELOPERS.map(d => <option key={d}>{d}</option>)}
                      </select>
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={labelStyle}>Priority</label>
                      <select style={inputStyle} value={iss.priority} disabled={readOnly} onChange={e => updateField(idx, 'priority', e.target.value)}>
                        {PRIORITIES.map(p => <option key={p}>{p}</option>)}
                      </select>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <div style={{ flex: 1 }}>
                      <label style={labelStyle}>Parent</label>
                      <input style={inputStyle} value={iss.parent} disabled={readOnly} onChange={e => updateField(idx, 'parent', e.target.value)} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={labelStyle}>Fix Version</label>
                      <input style={inputStyle} value={iss.fixVersion} disabled={readOnly} onChange={e => updateField(idx, 'fixVersion', e.target.value)} />
                    </div>
                  </div>

                  {iss.jiraUrl ? (
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                      Jira:{" "}
                      <a href={iss.jiraUrl} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-blue)', fontWeight: 700, textDecoration: 'none' }}>
                        Open
                      </a>
                    </div>
                  ) : null}

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '2px' }}>
                    <button
                      onClick={() => createIssue(idx)}
                      style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'none', border: '1px solid #4e26dc', borderRadius: '4px', padding: '3px 10px', cursor: 'pointer', fontSize: '0.75rem', color: '#26acdc' }}
                    >
                      <Trash2 size={11} /> Create
                    </button>

                    {iss.source === 'draft' && !iss.issueId ? (
                      <>
                        <button
                          onClick={() => toggleEdit(idx)}
                          style={{ border: '1px solid var(--border-color)', borderRadius: '6px', padding: '4px 14px', cursor: 'pointer', background: 'transparent', color: 'var(--text-primary)', fontSize: '0.78rem', fontWeight: 700 }}
                        >
                          {iss.isEditing ? 'Lock' : 'Edit'}
                        </button>

                        <button
                          onClick={() => createJira(idx)}
                          disabled={!iss.title.trim() || !iss.description.trim()}
                          className="run-button"
                          style={{ padding: '4px 14px', fontSize: '0.78rem' }}
                          title={(!iss.title.trim() || !iss.description.trim()) ? 'Title and Description required' : 'Create Jira ticket'}
                        >
                          Create
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => toggleEdit(idx)}
                        style={{ border: '1px solid var(--border-color)', borderRadius: '6px', padding: '4px 14px', cursor: 'pointer', background: 'transparent', color: 'var(--text-primary)', fontSize: '0.78rem', fontWeight: 700 }}
                      >
                        {iss.isEditing ? 'Lock' : 'Edit'}
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}