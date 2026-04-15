/**
 * JiraHistory.jsx
 *
 * Fixes:
 *  1. Uses ticket_type/type from API instead of hardcoding "created"
 *  2. Removed Refresh button
 *  3. Removed MongoDB health polling / MongoBanner / reconnect logic
 *  4. Removed status filter dropdown
 *  5. Module dropdown always shows ALL modules (client-side filtering)
 *  6. N/A / null ticketId all normalised → "Manual" group
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  History, ExternalLink, Search,
  ChevronDown, ChevronRight, Send, MessageSquare,
  CheckCircle, AlertCircle, Clock, LayoutList,
} from "lucide-react";

const API_URL = import.meta.env?.VITE_BACKEND_URL || "http://localhost:8000";

/* ─── helpers ──────────────────────────────────────────────────────────────── */
const fmt = (iso) => {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("en-IN", {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit", hour12: false,
    });
  } catch { return iso; }
};

/**
 * Normalise any "no ticket" value → null so all blanks bucket under "Manual".
 * Handles: null, undefined, "", "unknown", "N/A", "n/a", "null", "undefined", "-"
 */
const normaliseTicketId = (raw) => {
  if (!raw) return null;
  const s = String(raw).trim();
  if (!s || ["unknown", "n/a", "null", "undefined", "-"].includes(s.toLowerCase())) return null;
  return s;
};

const STATUS_COLORS = {
  Open:          { bg: "#eff6ff", text: "#1d4ed8" },
  "In Progress": { bg: "#faf5ff", text: "#7c3aed" },
  Done:          { bg: "#f0fdf4", text: "#15803d" },
  Assigned:      { bg: "#dcfce7", text: "#16a34a" },
  Unassigned:    { bg: "#f1f5f9", text: "#64748b" },
  Closed:        { bg: "#f1f5f9", text: "#475569" },
};

/* ─── shared UI ─────────────────────────────────────────────────────────────── */
const StatusBadge = ({ status }) => {
  const s   = STATUS_COLORS[status] || { bg: "#dbeafe", text: "#1d4ed8" };
  const icon =
    status === "Assigned"   ? <CheckCircle size={12} /> :
    status === "Unassigned" ? <AlertCircle size={12} /> :
    <Clock size={12} />;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      background: s.bg, color: s.text,
      borderRadius: 6, padding: "3px 10px",
      fontSize: "0.78rem", fontWeight: 700,
    }}>
      {icon} {status || "Assigned"}
    </span>
  );
};

const ModuleBadge = ({ module }) =>
  module
    ? <span style={{ background: "#ede9fe", color: "#7c3aed", borderRadius: 6, padding: "3px 10px", fontSize: "0.78rem", fontWeight: 700 }}>{module}</span>
    : <span style={{ color: "var(--text-secondary)" }}>—</span>;

const Avatar = ({ name, size = 28 }) => {
  const initials = (name || "?").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
  const COLORS   = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"];
  const bg       = COLORS[(name || "").charCodeAt(0) % COLORS.length];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      width: size, height: size, borderRadius: "50%",
      background: bg, color: "#fff",
      fontSize: size * 0.42 + "px", fontWeight: 700, flexShrink: 0,
    }}>
      {initials}
    </span>
  );
};

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

/* ─── IssueListCard ─────────────────────────────────────────────────────────── */
const IssueListCard = ({ issue, isSelected, onClick }) => {
  // ✅ FIX: use actual type from API, not hardcoded "created"
  const isAssigned = issue.type === "created";
  return (
    <div
      onClick={onClick}
      style={{
        padding: "10px 12px", cursor: "pointer",
        borderBottom: "1px solid var(--border-color)",
        background: isSelected ? "var(--input-bg)" : "transparent",
        borderLeft: isSelected ? "3px solid var(--accent-blue)" : "3px solid transparent",
        transition: "background 0.1s",
      }}
      onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = "var(--bg-console)"; }}
      onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = "transparent"; }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
        <span style={{
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          width: 20, height: 20, background: "var(--accent-blue)", borderRadius: 4, flexShrink: 0,
        }}>
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
      <div style={{
        fontSize: "0.75rem", color: "var(--text-secondary)",
        overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", paddingLeft: 26,
      }}>
        {issue.title || "Untitled"}
      </div>
    </div>
  );
};

/* ─── RunGroupList ──────────────────────────────────────────────────────────── */
const RunGroupList = ({ ticketId, issues, selectedId, onSelect }) => {
  const [open, setOpen] = useState(true);
  if (!issues.length) return null;

  const assignedCt   = issues.filter(h => h.type === "created").length;
  const unassignedCt = issues.filter(h => h.type === "removed").length;
  const label        = ticketId || "Manual";

  return (
    <div style={{ borderBottom: "1px solid var(--border-color)" }}>
      <button
        onClick={() => setOpen(v => !v)}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: 6,
          padding: "8px 12px",
          background: open ? "var(--input-bg)" : "var(--bg-console)",
          border: "none", cursor: "pointer", textAlign: "left",
          borderBottom: open ? "1px solid var(--border-color)" : "none",
        }}
      >
        {open
          ? <ChevronDown  size={12} color="var(--text-secondary)" />
          : <ChevronRight size={12} color="var(--text-secondary)" />}
        <span style={{
          fontSize: "0.72rem", fontWeight: 800,
          color: ticketId ? "var(--accent-blue)" : "var(--text-secondary)",
          fontFamily: "monospace", flex: 1,
          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
        }}>
          {label}
        </span>
        {assignedCt   > 0 && <span style={{ fontSize: "0.65rem", background: "#dcfce7", color: "#16a34a", borderRadius: 3, padding: "1px 5px", fontWeight: 700 }}>{assignedCt}✓</span>}
        {unassignedCt > 0 && <span style={{ fontSize: "0.65rem", background: "#f1f5f9", color: "#64748b", borderRadius: 3, padding: "1px 5px", fontWeight: 700 }}>{unassignedCt}○</span>}
      </button>

      {open && issues.map((h, i) => {
        const uid = h.issueId || h.internal_issue_id || `${label}-${i}`;
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

/* ─── DetailPanel ───────────────────────────────────────────────────────────── */
function DetailPanel({ issue, comments, onAddComment }) {
  const [commentText, setCommentText] = useState("");
  const [submitting,  setSubmitting]  = useState(false);
  const textRef = useRef(null);

  useEffect(() => { setCommentText(""); }, [issue?.issueId]);

  if (!issue) {
    return (
      <div style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        flexDirection: "column", gap: 12, color: "var(--text-secondary)",
      }}>
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

  const renderVersion = (v) => Array.isArray(v) ? v.join(", ") : (v || "");

  const fields = [
    { label: "Module",    value: <ModuleBadge module={issue.module} /> },
    { label: "Summary",   value: <span style={{ fontSize: "0.85rem", color: "var(--text-primary)" }}>{issue.title || "—"}</span> },
    { label: "Status",    value: <StatusBadge status={isAssigned ? "Assigned" : "Unassigned"} /> },
    {
      label: "Assignee",
      value: issue.developer && issue.developer !== "Unassigned"
        ? <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <Avatar name={issue.developer} size={22} />
            <span style={{ fontSize: "0.85rem" }}>{issue.developer}</span>
          </span>
        : <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Unassigned</span>,
    },
    {
      label: "Start Date",
      value: <span style={{ fontSize: "0.85rem", color: "var(--text-primary)" }}>
        {fmt(issue.start_date || issue.created_at || issue.savedAt)}
      </span>,
    },
    {
      label: "End Date",
      value: <span style={{ fontSize: "0.85rem", color: "var(--text-primary)" }}>
        {fmt(issue.end_date || issue.updated_at || issue.created_at || issue.savedAt)}
      </span>,
    },
    ...(issue.priority ? [{
      label: "Priority",
      value: <span style={{
        fontWeight: 700, fontSize: "0.85rem",
        color: issue.priority === "High" || issue.priority === "Critical" ? "#dc2626"
             : issue.priority === "Medium" ? "#d97706" : "#64748b",
      }}>{issue.priority}</span>,
    }] : []),
    ...(issue.app_version            ? [{ label: "App Version",     value: <span style={{ fontSize: "0.85rem" }}>{issue.app_version}</span>                    }] : []),
    ...(issue.test_name               ? [{ label: "Test",            value: <span style={{ fontSize: "0.85rem" }}>{issue.test_name}</span>                      }] : []),
    ...(issue.sprint                  ? [{ label: "Sprint",          value: <span style={{ fontSize: "0.85rem" }}>{issue.sprint}</span>                         }] : []),
    ...(issue.fix_version?.length     ? [{ label: "Fix Version",     value: <span style={{ fontSize: "0.85rem" }}>{renderVersion(issue.fix_version)}</span>     }] : []),
    ...(issue.affects_version?.length ? [{ label: "Affects Version", value: <span style={{ fontSize: "0.85rem" }}>{renderVersion(issue.affects_version)}</span> }] : []),
  ];

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      {/* Header */}
      <div style={{
        padding: "16px 20px", borderBottom: "1px solid var(--border-color)",
        display: "flex", alignItems: "center", gap: 10, flexShrink: 0,
      }}>
        <span style={{
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          width: 28, height: 28, background: "var(--accent-blue)", borderRadius: 6, flexShrink: 0,
        }}>
          <LayoutList size={14} color="#fff" />
        </span>
        <h2 style={{ margin: 0, fontSize: "1.3rem", fontWeight: 800, color: "var(--text-primary)" }}>
          {issue.issueId || issue.internal_issue_id || "Issue"}
        </h2>
        {issue.jiraUrl && isAssigned && (
          <a href={issue.jiraUrl} target="_blank" rel="noreferrer"
            style={{
              display: "inline-flex", alignItems: "center", color: "var(--accent-blue)",
              padding: 4, borderRadius: 4,
              border: "1px solid var(--border-color)", background: "var(--bg-card)",
            }}>
            <ExternalLink size={14} />
          </a>
        )}
      </div>

      {/* Scrollable body */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0 20px 20px" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", margin: "16px 0 0" }}>
          <tbody>
            {fields.map(f => (
              <tr key={f.label} style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{
                  padding: "10px 12px 10px 0", fontSize: "0.82rem",
                  fontWeight: 600, color: "var(--text-secondary)",
                  whiteSpace: "nowrap", verticalAlign: "middle", width: 140,
                }}>{f.label}</td>
                <td style={{ padding: "10px 0", verticalAlign: "middle" }}>{f.value}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Steps Executed */}
        {Array.isArray(issue.steps_executed) && issue.steps_executed.length > 0 && (
          <div style={{ marginTop: 20 }}>
            <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)", marginBottom: 8 }}>
              Steps Executed ({issue.steps_executed.length})
            </div>
            <ol style={{ margin: 0, paddingLeft: 20, fontSize: "0.82rem", color: "var(--text-primary)", lineHeight: 1.8 }}>
              {issue.steps_executed.map((s, i) => <li key={i}>{s}</li>)}
            </ol>
          </div>
        )}

        {/* Description */}
        {issue.description && (
          <div style={{ marginTop: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 10 }}>
              <div style={{ width: 20, height: 20, display: "inline-flex", alignItems: "center", justifyContent: "center", background: "var(--border-color)", borderRadius: 4 }}>
                <span style={{ fontSize: "0.7rem" }}>✏️</span>
              </div>
              <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)" }}>Description</span>
            </div>
            <div style={{
              background: "var(--bg-console)", borderRadius: 8,
              padding: "14px 16px", fontSize: "0.82rem",
              color: "var(--text-primary)", lineHeight: 1.7,
              whiteSpace: "pre-wrap", fontFamily: "inherit",
              border: "1px solid var(--border-color)",
            }}>
              {issue.description}
            </div>
          </div>
        )}

        {/* Comments */}
        <div style={{ marginTop: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 12 }}>
            <div style={{ width: 22, height: 22, display: "inline-flex", alignItems: "center", justifyContent: "center", background: "var(--accent-blue)", borderRadius: "50%" }}>
              <MessageSquare size={12} color="#fff" />
            </div>
            <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)" }}>
              Comments ({comments.length})
            </span>
          </div>

          {comments.length === 0 && (
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", padding: "8px 0" }}>
              No comments yet.
            </div>
          )}
          {comments.map((c, i) => (
            <div key={i} style={{ display: "flex", gap: 10, marginBottom: 14 }}>
              <Avatar name={c.author} size={30} />
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontWeight: 700, fontSize: "0.82rem", color: "var(--text-primary)" }}>{c.author}</span>
                  <span style={{ fontSize: "0.73rem", color: "var(--text-secondary)" }}>{fmt(c.created_at)}</span>
                </div>
                <div style={{ background: "var(--bg-console)", border: "1px solid var(--border-color)", borderRadius: 8, padding: "10px 12px", fontSize: "0.82rem", color: "var(--text-primary)", lineHeight: 1.6 }}>
                  {c.text}
                </div>
              </div>
            </div>
          ))}

          <div style={{ display: "flex", gap: 8, alignItems: "flex-end", marginTop: 4 }}>
            <textarea
              ref={textRef}
              value={commentText}
              onChange={e => setCommentText(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleSubmit(); }}
              placeholder="Add a comment…"
              rows={2}
              style={{
                flex: 1, resize: "vertical", padding: "10px 12px", borderRadius: 8,
                border: "1px solid var(--border-color)",
                background: "var(--bg-card)", color: "var(--text-primary)",
                fontSize: "0.82rem", lineHeight: 1.5, fontFamily: "inherit",
                outline: "none", minHeight: 48,
              }}
            />
            <button
              onClick={handleSubmit}
              disabled={!commentText.trim() || submitting}
              style={{
                width: 40, height: 40, flexShrink: 0,
                background: commentText.trim() ? "var(--accent-blue)" : "var(--border-color)",
                border: "none", borderRadius: 8,
                cursor: commentText.trim() ? "pointer" : "not-allowed",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "background 0.15s",
              }}
            >
              <Send size={16} color="#fff" />
            </button>
          </div>
          <div style={{ fontSize: "0.68rem", color: "var(--text-secondary)", marginTop: 4 }}>Ctrl+Enter to submit</div>
        </div>
      </div>
    </div>
  );
}

/* ─── JiraHistory — main export ─────────────────────────────────────────────── */
export default function JiraHistory({ issuePanelHistory = [], newTicket = null }) {
  const [apiIssues,     setApiIssues]     = useState([]);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState(null);
  const [source,        setSource]        = useState(null);
  const [search,        setSearch]        = useState("");
  const [activeTab,     setActiveTab]     = useState("all");
  const [filterModule,  setFilterModule]  = useState("");

  // Full module list — NEVER overwritten by filter changes
  const [allModules,    setAllModules]    = useState([]);

  const [selectedId,    setSelectedId]    = useState(null);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [comments,      setComments]      = useState([]);

  // ── Fetch ALL tickets — no backend filtering ────────────────────────────
  const fetchIssues = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/jira/history?limit=500`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data   = await res.json();
      const issues = data.issues ?? [];
      setApiIssues(issues);
      setSource(data.source || "unknown");
      setAllModules([...new Set(issues.map(t => t.module).filter(Boolean))].sort());
    } catch (err) {
      try {
        const r2 = await fetch(`${API_URL}/jira/history`);
        if (r2.ok) {
          const d2 = await r2.json();
          const issues2 = d2.issues ?? [];
          setApiIssues(issues2);
          setAllModules([...new Set(issues2.map(t => t.module).filter(Boolean))].sort());
          return;
        }
      } catch { /* ignore */ }
      setError(err.message || "Could not reach server");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchIssues(); }, [fetchIssues]);

  // Prepend new ticket from IssuePanel
  useEffect(() => {
    if (!newTicket) return;
    setApiIssues(prev => {
      if (prev.some(t => t.issue_id === newTicket.issue_id)) return prev;
      if (newTicket.module) {
        setAllModules(m => [...new Set([...m, newTicket.module])].sort());
      }
      return [newTicket, ...prev];
    });
  }, [newTicket]);

  // Comments
  useEffect(() => {
    if (!selectedIssue?.issueId) { setComments([]); return; }
    fetch(`${API_URL}/api/jira/comments/${selectedIssue.issueId}`)
      .then(r => r.json())
      .then(d => setComments(d.comments || []))
      .catch(() => setComments([]));
  }, [selectedIssue?.issueId]);

  // Live comment updates via WebSocket
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
              return exists ? prev : [...prev, msg.payload.comment];
            });
          }
        } catch { /* ignore */ }
      };
    } catch { /* ignore */ }
    return () => { try { ws?.close(); } catch { /* ignore */ } };
  }, [selectedIssue?.issueId]);

  const addComment = async (issueKey, text) => {
    if (!issueKey) return;
    try {
      await fetch(`${API_URL}/api/jira/comments/${issueKey}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, author: selectedIssue?.developer || "QA Automation" }),
      });
    } catch { /* ignore */ }
  };

  const handleSelect = (uid, issue) => {
    setSelectedId(uid);
    setSelectedIssue(issue);
    setComments([]);
  };

  // ✅ FIX: Use ticket_type/type from API response, NOT hardcoded "created"
  const apiEntries = apiIssues.map(i => ({
    type:              i.ticket_type || i.type || "created",   // ← key fix
    ticketId:          normaliseTicketId(i.ticket_id),
    issueId:           i.issue_id           || i.key      || "",
    jiraUrl:           i.issue_url          || i.url      || "",
    title:             i.title              || i.summary  || "Untitled",
    module:            i.module             || "",
    developer:         i.developer_name     || i.assignee || "",
    priority: (i.ticket_type || i.type) === "removed"? "NA"
    : (i.priority ?? null),
    internal_issue_id: i.internal_issue_id  || "",
    description:       i.description        || "",
    app_name:          i.app_name           || "",
    app_version:       i.app_version        || "",
    test_name:         i.test_name          || "",
    sprint:            i.sprint             || "",
    steps_executed:    Array.isArray(i.steps_executed)  ? i.steps_executed  : [],
    fix_version:       Array.isArray(i.fix_version)     ? i.fix_version     : [],
    affects_version:   Array.isArray(i.affects_version) ? i.affects_version : [],
    start_date:        i.start_date         || "",
    end_date:          i.end_date           || i.due_date || "",
    created_at:        i.created_at         || "",
    savedAt:           i.created_at         || "",
  }));

  // Merge with real-time panel history
  const panelCreatedIds = new Set(
    issuePanelHistory.filter(h => h.type === "created" && h.issueId).map(h => h.issueId)
  );
  const allHistory = [
    ...issuePanelHistory.map(h => ({
      ...h,
      ticketId: normaliseTicketId(h.ticketId),
    })),
    ...apiEntries.filter(e => !panelCreatedIds.has(e.issueId)),
  ];

  // Client-side filtering only
  const filteredHistory = allHistory.filter(h => {
    const matchTab =
      activeTab === "all" ||
      (activeTab === "assigned"   && h.type === "created") ||
      (activeTab === "unassigned" && h.type === "removed");
    if (!matchTab) return false;

    if (filterModule && (h.module || "").toLowerCase() !== filterModule.toLowerCase()) return false;

    if (search) {
      const q = search.toLowerCase();
      return (
        (h.issueId   || "").toLowerCase().includes(q) ||
        (h.title     || "").toLowerCase().includes(q) ||
        (h.module    || "").toLowerCase().includes(q) ||
        (h.developer || "").toLowerCase().includes(q) ||
        (h.test_name || "").toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Group by ticketId (null → __manual__ bucket)
  const groupedMap = {};
  filteredHistory.forEach(h => {
    const key = h.ticketId ?? "__manual__";
    if (!groupedMap[key]) groupedMap[key] = [];
    groupedMap[key].push(h);
  });

  // Sort: real IDs descending, manual last
  const sortedTicketIds = Object.keys(groupedMap).sort((a, b) => {
    if (a === "__manual__") return 1;
    if (b === "__manual__") return -1;
    return b.localeCompare(a);
  });

  // Clear selection if filtered out
  const visibleIssues = sortedTicketIds.flatMap(k => groupedMap[k] || []);
  useEffect(() => {
    const stillVisible = selectedIssue && visibleIssues.some(h =>
      (h.issueId || h.internal_issue_id) === selectedId
    );
    if (selectedIssue && !stillVisible) {
      setSelectedId(null);
      setSelectedIssue(null);
      setComments([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, search, filterModule]);

  // Summary counts — always from full unfiltered history
  const totalAssigned   = allHistory.filter(h => h.type === "created").length;
  const totalUnassigned = allHistory.filter(h => h.type === "removed").length;
  const total           = allHistory.length;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 80px)", gap: "1rem" }}>
{/* 
      Page header — NO Refresh button */}
      <div style={{ display: "flex", alignItems: "center", flexShrink: 0 }}>
        {/* <History size={22} color="var(--accent-blue)" /> */}
        <h1 style={{ margin: "0 0 0 10px", fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
          Jira History
        </h1>
        {source && (
          <span style={{ fontSize: "0.72rem", color: source === "mongodb" ? "#16a34a" : "var(--text-secondary)", marginLeft: 14 }}>
            {source === "mongodb" ? `✅ MongoDB — ${total} ticket${total !== 1 ? "s" : ""}` : `⚠️ Session memory (${total})`}
          </span>
        )}
      </div>

      {/* Summary cards */}
      <div style={{ display: "flex", gap: "1rem", flexShrink: 0 }}>
        {[
          { label: "Total Issues", value: total,           color: "var(--accent-blue)" },
          { label: "Assigned",     value: totalAssigned,   color: "#d97706" },
          { label: "Unassigned",   value: totalUnassigned, color: "#64748b" },
        ].map(c => (
          <div key={c.label} className="dashboard-card" style={{ flex: 1 }}>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: 4 }}>{c.label}</div>
          </div>
        ))}
      </div>

      {/* Search + module filter + tab pills — NO status dropdown, NO chevron dropdown */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexShrink: 0, flexWrap: "wrap" }}>
        <div style={{ flex: 1, position: "relative", minWidth: 200 }}>
          <Search size={14} style={{ position: "absolute", left: 11, top: "50%", transform: "translateY(-50%)", color: "var(--text-secondary)" }} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by key, summary, assignee…"
            style={{
              width: "100%", boxSizing: "border-box",
              paddingLeft: 32, paddingRight: 12, paddingTop: 9, paddingBottom: 9,
              borderRadius: 8, border: "1px solid var(--border-color)",
              background: "var(--bg-card)", color: "var(--text-primary)",
              fontSize: "0.875rem", outline: "none",
            }}
          />
        </div>

        {/* Module dropdown — always full list */}
        <select
          value={filterModule}
          onChange={e => setFilterModule(e.target.value)}
          style={{
            padding: "7px 10px", border: "1px solid var(--border-color)",
            borderRadius: 8, fontSize: "0.82rem",
            background: "var(--bg-card)", color: "var(--text-primary)",
            cursor: "pointer",
          }}
        >
          <option value="">All Modules</option>
          {allModules.map(m => <option key={m} value={m}>{m}</option>)}
        </select>

        {/* Tab pills only — no extra dropdown buttons */}
        <div style={{ display: "flex", gap: 6 }}>
          <PillBtn active={activeTab === "all"}        onClick={() => setActiveTab("all")}>All</PillBtn>
          <PillBtn active={activeTab === "assigned"}   onClick={() => setActiveTab("assigned")}>Assigned</PillBtn>
          <PillBtn active={activeTab === "unassigned"} onClick={() => setActiveTab("unassigned")}>Unassigned</PillBtn>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div style={{
          background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8,
          padding: "10px 14px", color: "#b91c1c", fontSize: "0.85rem",
          flexShrink: 0, display: "flex", alignItems: "center", gap: 10,
        }}>
          <span>⚠️ {error}</span>
          <button onClick={fetchIssues} style={{
            marginLeft: "auto", color: "#b91c1c", textDecoration: "underline",
            background: "none", border: "none", cursor: "pointer", fontSize: "0.85rem",
          }}>Retry</button>
        </div>
      )}

      {/* Split pane */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden", border: "1px solid var(--border-color)", borderRadius: 12 }}>

        {/* LEFT: issue list */}
        <div style={{ width: 340, flexShrink: 0, borderRight: "1px solid var(--border-color)", overflowY: "auto", background: "var(--bg-card)" }}>
          {loading && sortedTicketIds.length === 0 ? (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--text-secondary)" }}>Loading…</div>
          ) : sortedTicketIds.length === 0 ? (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
              {search || filterModule
                ? "No issues match your filters."
                : "No issues yet. Run a test to create one."}
            </div>
          ) : (
            sortedTicketIds.map(key => (
              <RunGroupList
                key={key}
                ticketId={key === "__manual__" ? null : key}
                issues={groupedMap[key]}
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