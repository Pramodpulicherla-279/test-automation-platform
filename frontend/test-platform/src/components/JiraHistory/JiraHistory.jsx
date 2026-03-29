/**
 * JiraHistory.jsx
 *
 * Split-pane layout matching the design:
 *   LEFT:  issue list grouped by ticket_id (Run ID), tabs All/Assigned/Unassigned
 *          summary cards: Total / Assigned / Unassigned
 *          search bar
 *   RIGHT: detail panel for selected issue
 *          - Module, Summary, Status, Assignee, Creation Date, Last Updated
 *          - Description
 *          - Comments (with add comment)
 */

import React, { useState, useEffect, useRef } from "react";
import {
  History, ExternalLink, RefreshCw, Search,
  ChevronDown, ChevronRight, Send, MessageSquare,
  CheckCircle, AlertCircle, Clock, LayoutList,
} from "lucide-react";

const API_URL = "http://localhost:8000";

/* ─── Helpers ─────────────────────────────────────────────────────────────── */
const fmt = (iso) => {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleString("en-IN", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }); }
  catch { return iso; }
};

const StatusBadge = ({ status }) => {
  const cfg =
    status === "Assigned" ? { bg: "#dcfce7", color: "#16a34a", icon: <CheckCircle size={12} /> } :
      status === "Unassigned" ? { bg: "#f1f5f9", color: "#64748b", icon: <AlertCircle size={12} /> } :
        { bg: "#dbeafe", color: "#1d4ed8", icon: <Clock size={12} /> };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, background: cfg.bg, color: cfg.color, borderRadius: 6, padding: "3px 10px", fontSize: "0.78rem", fontWeight: 700 }}>
      {cfg.icon} {status || "Assigned"}
    </span>
  );
};

const ModuleBadge = ({ module }) => module ? (
  <span style={{ background: "#ede9fe", color: "#7c3aed", borderRadius: 6, padding: "3px 10px", fontSize: "0.78rem", fontWeight: 700 }}>{module}</span>
) : <span style={{ color: "var(--text-secondary)" }}>—</span>;

const Avatar = ({ name, size = 28 }) => {
  const initials = (name || "?").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
  const colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"];
  const bg = colors[(name || "").charCodeAt(0) % colors.length];
  return (
    <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: size, height: size, borderRadius: "50%", background: bg, color: "#fff", fontSize: size * 0.42 + "px", fontWeight: 700, flexShrink: 0 }}>
      {initials}
    </span>
  );
};

/* ─── Left panel ──────────────────────────────────────────────────────────── */
const PillBtn = ({ active, onClick, children }) => (
  <button onClick={onClick} style={{
    padding: "5px 14px", borderRadius: "999px",
    border: "1px solid var(--border-color)",
    cursor: "pointer", fontSize: "0.78rem",
    fontWeight: active ? 700 : 400,
    background: active ? "var(--accent-blue)" : "var(--bg-card)",
    color: active ? "#fff" : "var(--text-secondary)",
    transition: "all 0.12s",
  }}>
    {children}
  </button>
);

/* Issue card in left list */
const IssueListCard = ({ issue, isSelected, onClick }) => {
  const isAssigned = issue.type === "created";
  return (
    <div onClick={onClick} style={{
      padding: "10px 12px", cursor: "pointer",
      borderBottom: "1px solid var(--border-color)",
      background: isSelected ? "var(--input-bg)" : "transparent",
      borderLeft: isSelected ? "3px solid var(--accent-blue)" : "3px solid transparent",
      transition: "background 0.1s",
    }}
      onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = "var(--bg-console)"; }}
      onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = "transparent"; }}>
      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "3px" }}>
        <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 20, height: 20, background: "var(--accent-blue)", borderRadius: 4, flexShrink: 0 }}>
          <LayoutList size={11} color="#fff" />
        </span>
        <span style={{ fontWeight: 700, fontSize: "0.8rem", color: isAssigned ? "var(--accent-blue)" : "var(--text-secondary)" }}>
          {issue.issueId || issue.internal_issue_id || "—"}
        </span>
        {issue.jiraUrl && isAssigned && (
          <a href={issue.jiraUrl} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
            style={{ color: "var(--accent-blue)", display: "inline-flex", alignItems: "center" }}>
            <ExternalLink size={10} />
          </a>
        )}
        <div style={{ flex: 1 }} />
        <StatusBadge status={isAssigned ? "Assigned" : "Unassigned"} />
      </div>
      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", paddingLeft: 26 }}>
        {issue.title || "Untitled"}
      </div>
    </div>
  );
};

/* Run group in left list */
const RunGroupList = ({ ticketId, issues, filter, search, selectedId, onSelect }) => {
  const [open, setOpen] = useState(true);

  const filtered = issues;
  if (filtered.length === 0) return null;

  const assignedCt = filtered.filter(h => h.type === "created").length;
  const unassignedCt = filtered.filter(h => h.type === "removed").length;

  return (
    <div style={{ borderBottom: "1px solid var(--border-color)" }}>
      <button onClick={() => setOpen(v => !v)} style={{
        width: "100%", display: "flex", alignItems: "center", gap: "6px",
        padding: "8px 12px",
        background: open ? "var(--input-bg)" : "var(--bg-console)",
        border: "none", cursor: "pointer", textAlign: "left",
        borderBottom: open ? "1px solid var(--border-color)" : "none",
      }}>
        {open ? <ChevronDown size={12} color="var(--text-secondary)" /> : <ChevronRight size={12} color="var(--text-secondary)" />}
        <span style={{ fontSize: "0.72rem", fontWeight: 800, color: "var(--accent-blue)", fontFamily: "monospace", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {ticketId || "Manual"}
        </span>
        {assignedCt > 0 && <span style={{ fontSize: "0.65rem", background: "#dcfce7", color: "#16a34a", borderRadius: 3, padding: "1px 5px", fontWeight: 700 }}>{assignedCt}✓</span>}
        {unassignedCt > 0 && <span style={{ fontSize: "0.65rem", background: "#f1f5f9", color: "#64748b", borderRadius: 3, padding: "1px 5px", fontWeight: 700 }}>{unassignedCt}○</span>}
      </button>

      {open && filtered.map((h, i) => {
        const uid = h.issueId || h.internal_issue_id || `${ticketId}-${i}`;
        return (
          <IssueListCard
            key={uid}
            issue={h}
            isSelected={selectedId === uid}
            onClick={() => onSelect(uid, h)}
          />
        );
      })}
    </div>
  );
};

/* ─── Right panel — detail view ───────────────────────────────────────────── */
function DetailPanel({ issue, comments, onAddComment }) {
  const [commentText, setCommentText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const textRef = useRef(null);

  if (!issue) {
    return (
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 12, color: "var(--text-secondary)" }}>
        <MessageSquare size={40} strokeWidth={1.2} />
        <div style={{ fontSize: "0.9rem" }}>Select an issue to view details</div>
      </div>
    );
  }

  const isAssigned = issue.type === "created";

  const handleSubmit = async () => {
    const text = commentText.trim();
    if (!text || submitting) return;
    setSubmitting(true);
    await onAddComment(issue.issueId, text);
    setCommentText("");
    setSubmitting(false);
    textRef.current?.focus();
  };

  // ── Helper to render version arrays ──────────────────────────────────────
  const renderVersion = (v) =>
    Array.isArray(v) ? v.join(", ") : (v || "");

  const fields = [
    { label: "Module",      value: <ModuleBadge module={issue.module} /> },
    { label: "Summary",     value: <span style={{ fontSize: "0.85rem", color: "var(--text-primary)" }}>{issue.title || "—"}</span> },
    { label: "Status",      value: <StatusBadge status={isAssigned ? "Assigned" : "Unassigned"} /> },
    {
      label: "Assignee",
      value: issue.developer && issue.developer !== "Unassigned"
        ? <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <Avatar name={issue.developer} size={22} />
            <span style={{ fontSize: "0.85rem" }}>{issue.developer}</span>
          </span>
        : <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Unassigned</span>
    },
    {
      label: "Start Date",
      value: <span style={{ fontSize: "0.85rem", color: "var(--text-primary)" }}>
        {fmt(issue.start_date || issue.created_at || issue.savedAt)}
      </span>
    },
    {
      label: "Last Updated",
      value: <span style={{ fontSize: "0.85rem", color: "var(--text-primary)" }}>
        {fmt(issue.end_date || issue.updated_at || issue.created_at || issue.savedAt)}
      </span>
    },
    ...(issue.priority ? [{
      label: "Priority",
      value: <span style={{ fontWeight: 700, fontSize: "0.85rem", color: issue.priority === "High" ? "#dc2626" : issue.priority === "Medium" ? "#d97706" : "#64748b" }}>
        {issue.priority}
      </span>
    }] : []),
    ...(issue.app_version ? [{
      label: "App Version",
      value: <span style={{ fontSize: "0.85rem" }}>{issue.app_version}</span>
    }] : []),
    ...(issue.sprint ? [{
      label: "Sprint",
      value: <span style={{ fontSize: "0.85rem" }}>{issue.sprint}</span>
    }] : []),
    // ── Fix Version ──────────────────────────────────────────────────────────
    ...(issue.fix_version && issue.fix_version.length ? [{
      label: "Fix Version",
      value: <span style={{ fontSize: "0.85rem" }}>{renderVersion(issue.fix_version)}</span>
    }] : []),
    // ── Affects Version ─────────────────────────────────────────────────────
    ...(issue.affects_version && issue.affects_version.length ? [{
      label: "Affects Version",
      value: <span style={{ fontSize: "0.85rem" }}>{renderVersion(issue.affects_version)}</span>
    }] : []),
  ];

  const steps = Array.isArray(issue.steps_executed) ? issue.steps_executed : [];

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

      {/* Header */}
      <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border-color)", display: "flex", alignItems: "center", gap: "10px", flexShrink: 0 }}>
        <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 28, height: 28, background: "var(--accent-blue)", borderRadius: 6, flexShrink: 0 }}>
          <LayoutList size={14} color="#fff" />
        </span>
        <h2 style={{ margin: 0, fontSize: "1.3rem", fontWeight: 800, color: "var(--text-primary)" }}>
          {issue.issueId || issue.internal_issue_id || "Issue"}
        </h2>
        {issue.jiraUrl && isAssigned && (
          <a href={issue.jiraUrl} target="_blank" rel="noreferrer"
            style={{ display: "inline-flex", alignItems: "center", color: "var(--accent-blue)", padding: 4, borderRadius: 4, border: "1px solid var(--border-color)", background: "var(--bg-card)" }}>
            <ExternalLink size={14} />
          </a>
        )}
      </div>

      {/* Scrollable body */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0 20px 20px" }}>

        {/* Fields table */}
        <table style={{ width: "100%", borderCollapse: "collapse", margin: "16px 0 0" }}>
          <tbody>
            {fields.map(f => (
              <tr key={f.label} style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "10px 12px 10px 0", fontSize: "0.82rem", fontWeight: 600, color: "var(--text-secondary)", whiteSpace: "nowrap", verticalAlign: "middle", width: 140 }}>
                  {f.label}
                </td>
                <td style={{ padding: "10px 0", verticalAlign: "middle" }}>
                  {f.value}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Description */}
        {issue.description && (
          <div style={{ marginTop: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: "10px" }}>
              <div style={{ width: 20, height: 20, display: "inline-flex", alignItems: "center", justifyContent: "center", background: "var(--border-color)", borderRadius: 4 }}>
                <span style={{ fontSize: "0.7rem" }}>✏️</span>
              </div>
              <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)" }}>Description</span>
            </div>
            <div style={{ background: "var(--bg-console)", borderRadius: 8, padding: "14px 16px", fontSize: "0.82rem", color: "var(--text-primary)", lineHeight: "1.7", whiteSpace: "pre-wrap", fontFamily: "inherit", border: "1px solid var(--border-color)" }}>
              {issue.description}
            </div>
          </div>
        )}

        {/* Comments */}
        <div style={{ marginTop: "24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: "12px" }}>
            <div style={{ width: 22, height: 22, display: "inline-flex", alignItems: "center", justifyContent: "center", background: "var(--accent-blue)", borderRadius: "50%" }}>
              <MessageSquare size={12} color="#fff" />
            </div>
            <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)" }}>
              Comments ({comments.length})
            </span>
          </div>

          {comments.length === 0 && (
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", padding: "8px 0" }}>No comments yet.</div>
          )}
          {comments.map((c, i) => (
            <div key={i} style={{ display: "flex", gap: "10px", marginBottom: "14px" }}>
              <Avatar name={c.author} size={30} />
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                  <span style={{ fontWeight: 700, fontSize: "0.82rem", color: "var(--text-primary)" }}>{c.author}</span>
                  <span style={{ fontSize: "0.73rem", color: "var(--text-secondary)" }}>{fmt(c.created_at)}</span>
                </div>
                <div style={{ background: "var(--bg-console)", border: "1px solid var(--border-color)", borderRadius: 8, padding: "10px 12px", fontSize: "0.82rem", color: "var(--text-primary)", lineHeight: "1.6" }}>
                  {c.text}
                </div>
              </div>
            </div>
          ))}

          {/* Add comment */}
          <div style={{ display: "flex", gap: "8px", alignItems: "flex-end", marginTop: "4px" }}>
            <textarea
              ref={textRef}
              value={commentText}
              onChange={e => setCommentText(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleSubmit(); }}
              placeholder="Add a comment…"
              rows={2}
              style={{
                flex: 1, resize: "vertical",
                padding: "10px 12px", borderRadius: 8,
                border: "1px solid var(--border-color)",
                background: "var(--bg-card)",
                color: "var(--text-primary)",
                fontSize: "0.82rem", lineHeight: "1.5",
                fontFamily: "inherit",
                outline: "none",
                minHeight: 48,
              }}
            />
            <button
              onClick={handleSubmit}
              disabled={!commentText.trim() || submitting}
              style={{
                width: 40, height: 40, flexShrink: 0,
                background: commentText.trim() ? "var(--accent-blue)" : "var(--border-color)",
                border: "none", borderRadius: 8, cursor: commentText.trim() ? "pointer" : "not-allowed",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "background 0.15s",
              }}>
              <Send size={16} color="#fff" />
            </button>
          </div>
          <div style={{ fontSize: "0.68rem", color: "var(--text-secondary)", marginTop: 4 }}>Ctrl+Enter to submit</div>
        </div>

      </div>
    </div>
  );
}

/* ─── JiraHistory (main) ──────────────────────────────────────────────────── */
export default function JiraHistory({ issuePanelHistory = [] }) {
  const [apiIssues, setApiIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const [selectedId, setSelectedId] = useState(null);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [comments, setComments] = useState([]);

  const fetchIssues = async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${API_URL}/api/jira/history`);
      if (!res.ok) throw new Error(`${res.status}`);
      setApiIssues((await res.json()).issues ?? []);
    } catch {
      try {
        const r2 = await fetch(`${API_URL}/jira/history`);
        if (r2.ok) { setApiIssues((await r2.json()).issues ?? []); return; }
      } catch { }
      setError("Could not fetch from server");
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchIssues(); }, []);

  useEffect(() => {
    if (!selectedIssue?.issueId) { setComments([]); return; }
    fetch(`${API_URL}/api/jira/comments/${selectedIssue.issueId}`)
      .then(r => r.json())
      .then(d => setComments(d.comments || []))
      .catch(() => setComments([]));
  }, [selectedIssue?.issueId]);

  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket("ws://localhost:8000/ws/test-status");
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          if (msg.type === "JIRA_COMMENT" && msg.payload?.issue_key === selectedIssue?.issueId) {
            setComments(prev => {
              const exists = prev.some(
                c => c.text === msg.payload.comment.text && c.created_at === msg.payload.comment.created_at
              );
              if (exists) return prev;
              return [...prev, msg.payload.comment];
            });
          }
        } catch { }
      };
    } catch { }
    return () => { try { ws?.close(); } catch { } };
  }, [selectedIssue?.issueId]);

  const addComment = async (issueKey, text) => {
    if (!issueKey) return;
    try {
      await fetch(`${API_URL}/api/jira/comments/${issueKey}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, author: selectedIssue?.developer || "QA Automation" }),
      });
    } catch { }
  };

  const handleSelect = (uid, issue) => {
    setSelectedId(uid);
    setSelectedIssue(issue);
    setComments([]);
  };

  // ── Build unified history from API + real-time panel history ───────────────
  const apiEntries = apiIssues.map(i => ({
    type:              "created",
    ticketId:          i.ticket_id          || "unknown",
    issueId:           i.issue_id           || i.key        || "",
    jiraUrl:           i.issue_url          || i.url        || "",
    title:             i.title              || i.summary    || "Untitled",
    module:            i.module             || "",
    developer:         i.developer_name     || i.assignee   || "",
    priority:          i.priority           || "High",
    internal_issue_id: i.internal_issue_id  || "",
    description:       i.description        || "",
    app_name:          i.app_name           || "",
    app_version:       i.app_version        || "",
    test_name:         i.test_name          || "",
    sprint:            i.sprint             || "",
    steps_executed:    Array.isArray(i.steps_executed)  ? i.steps_executed  : [],
    // ── FIX: both version arrays now mapped ─────────────────────────────────
    fix_version:       Array.isArray(i.fix_version)     ? i.fix_version     : [],
    affects_version:   Array.isArray(i.affects_version) ? i.affects_version : [],
    // ── Dates ────────────────────────────────────────────────────────────────
    start_date:        i.start_date         || "",
    end_date:          i.end_date           || "",
    created_at:        i.created_at         || "",
    savedAt:           i.created_at         || "",
  }));

  const panelCreatedIds = new Set(
    issuePanelHistory.filter(h => h.type === "created" && h.issueId).map(h => h.issueId)
  );
  const mergedApi = apiEntries.filter(e => !panelCreatedIds.has(e.issueId));
  const allHistory = [...issuePanelHistory, ...mergedApi];

  const filteredHistory = allHistory.filter(h => {
    const matchTab =
      activeTab === "all" ||
      (activeTab === "assigned"   && h.type === "created") ||
      (activeTab === "unassigned" && h.type === "removed");
    if (!matchTab) return false;
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (h.issueId    || "").toLowerCase().includes(q) ||
      (h.title      || "").toLowerCase().includes(q) ||
      (h.module     || "").toLowerCase().includes(q) ||
      (h.developer  || "").toLowerCase().includes(q)
    );
  });

  const groupedMap = {};
  filteredHistory.forEach(h => {
    const tid = h.ticketId || "unknown";
    if (!groupedMap[tid]) groupedMap[tid] = [];
    groupedMap[tid].push(h);
  });
  const sortedTicketIds = Object.keys(groupedMap).sort((a, b) => b.localeCompare(a));

  const visibleIssues = sortedTicketIds.flatMap(tid => groupedMap[tid] || []);
  const selectedStillVisible = selectedIssue && visibleIssues.some(h => {
    const uid = h.issueId || h.internal_issue_id;
    return uid && uid === selectedId;
  });

  useEffect(() => {
    if (selectedIssue && !selectedStillVisible) {
      setSelectedId(null);
      setSelectedIssue(null);
      setComments([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, search, selectedStillVisible]);

  const totalAssigned   = allHistory.filter(h => h.type === "created").length;
  const totalUnassigned = allHistory.filter(h => h.type === "removed").length;
  const total           = allHistory.length;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 80px)", gap: "1rem" }}>

      {/* Page header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <History size={22} color="var(--accent-blue)" />
          <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>Jira History</h1>
        </div>
        <button onClick={fetchIssues} disabled={loading} style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--accent-blue)", color: "#fff", border: "none", borderRadius: 8, padding: "8px 16px", cursor: "pointer", fontSize: "0.875rem", fontWeight: 600 }}>
          <RefreshCw size={14} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
          Refresh
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display: "flex", gap: "1rem", flexShrink: 0 }}>
        {[
          { label: "Total Issues", value: total,          color: "var(--accent-blue)" },
          { label: "Assigned",     value: totalAssigned,  color: "#d97706" },
          { label: "Unassigned",   value: totalUnassigned, color: "#64748b" },
        ].map(c => (
          <div key={c.label} className="dashboard-card" style={{ flex: 1 }}>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: 4 }}>{c.label}</div>
          </div>
        ))}
      </div>

      {/* Search + Tabs */}
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexShrink: 0, flexWrap: "wrap" }}>
        <div style={{ flex: 1, position: "relative", minWidth: 200 }}>
          <Search size={14} style={{ position: "absolute", left: 11, top: "50%", transform: "translateY(-50%)", color: "var(--text-secondary)" }} />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search by key, summary, assignee…"
            style={{ width: "100%", boxSizing: "border-box", paddingLeft: 32, paddingRight: 12, paddingTop: 9, paddingBottom: 9, borderRadius: 8, border: "1px solid var(--border-color)", background: "var(--bg-card)", color: "var(--text-primary)", fontSize: "0.875rem" }} />
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <PillBtn active={activeTab === "all"}        onClick={() => setActiveTab("all")}>All</PillBtn>
          <PillBtn active={activeTab === "assigned"}   onClick={() => setActiveTab("assigned")}>Assigned</PillBtn>
          <PillBtn active={activeTab === "unassigned"} onClick={() => setActiveTab("unassigned")}>Unassigned</PillBtn>
          <button style={{ width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid var(--border-color)", borderRadius: 8, background: "var(--bg-card)", cursor: "pointer" }}>
            <ChevronDown size={14} color="var(--text-secondary)" />
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: "10px 14px", color: "#b91c1c", fontSize: "0.85rem", flexShrink: 0 }}>
          ⚠️ {error}
        </div>
      )}

      {/* Main split-pane */}
      <div style={{ flex: 1, display: "flex", gap: 0, overflow: "hidden", border: "1px solid var(--border-color)", borderRadius: 12 }}>

        {/* LEFT: issue list */}
        <div style={{ width: 340, flexShrink: 0, borderRight: "1px solid var(--border-color)", overflowY: "auto", background: "var(--bg-card)" }}>
          {sortedTicketIds.length === 0 ? (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--text-secondary)" }}>
              {loading ? "Loading…" : "No issues yet."}
            </div>
          ) : (
            sortedTicketIds.map(tid => (
              <RunGroupList
                key={tid}
                ticketId={tid === "unknown" ? "" : tid}
                issues={groupedMap[tid]}
                filter={activeTab}
                search={search}
                selectedId={selectedId}
                onSelect={handleSelect}
              />
            ))
          )}
        </div>

        {/* RIGHT: detail panel */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden", background: "var(--bg-card)" }}>
          <DetailPanel
            issue={selectedIssue}
            comments={comments}
            onAddComment={addComment}
          />
        </div>

      </div>
    </div>
  );
}