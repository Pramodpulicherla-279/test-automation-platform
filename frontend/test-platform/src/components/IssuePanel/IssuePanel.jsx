/**
 * IssuePanel.jsx
 *
 * Key fixes:
 *  1. Issues persisted in sessionStorage → survive route navigation (/ → /jira-history → /)
 *  2. On new test run (server clears payloads), IssuePanel also clears via WS message "RUN_START"
 *  3. Dismissed payloads POSTed to /api/jira/dismiss on Remove AND Create
 *  4. Dedup uses test_name+module — stable across restarts
 *  5. Issue ID shown as ISS-001 format
 *  6. Remove → JiraHistory Unassigned via onHistoryUpdate
 *  7. Create → removed from panel, JiraHistory Assigned via onHistoryUpdate
 *  8. On page refresh: only active (non-dismissed) payloads restored from server
 */

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  AlertCircle, ChevronDown, ChevronRight,
  ExternalLink, Maximize2, Minimize2, Plus, Wifi, WifiOff,
} from "lucide-react";

const BACKEND    = "http://localhost:8000";
const WS_BACKEND = "ws://localhost:8000/ws/test-status";
const SS_KEY     = "issuePanelIssues";   // sessionStorage key

const DEVELOPERS     = ["Unassigned", "Anuj", "Vaibhav", "Vikash", "Swaroopa", "Krishivaas"];
const PRIORITIES     = ["High", "Medium", "Low"];
const PRIORITY_COLOR = { High: "#dc2626", Medium: "#d97706", Low: "#64748b" };

/* ─── Helpers ─────────────────────────────────────────────────────────────── */
const safeStr = (v) => (v == null ? "" : String(v));

const pickFirst = (obj, keys) => {
  for (const k of keys) {
    const v = obj?.[k];
    if (v != null && String(v).trim()) return v;
  }
  return "";
};

/**
 * Stable dedup key — uses test_name+module (never changes across formats).
 * Falls back to issue_summary+module if test_name is absent.
 */
const dedupKey = (p) => {
  const tn = safeStr(p?.test_name || "").trim();
  const md = safeStr(p?.module    || "").trim();
  if (tn) return `tn::${md}::${tn}`;
  const sm = safeStr(p?.issue_summary || p?.title || "").trim();
  return `sum::${md}::${sm}`;
};

const parsePayloadFromLogLine = (line) => {
  for (const prefix of ["JIRA_PAYLOAD_JSON:", "AUTOMATION_PAYLOAD_JSON:"]) {
    if (typeof line === "string" && line.startsWith(prefix)) {
      try { return JSON.parse(line.slice(prefix.length).trim()); }
      catch (_) {}
    }
  }
  return null;
};

const toArr = (v) => {
  if (!v) return [];
  if (Array.isArray(v)) return v.filter(Boolean).map(String);
  return [String(v)].filter(Boolean);
};

const emptyIssue = () => ({
  source: "manual",
  jiraUrl: "", issueId: "", title: "", description: "",
  developer: "Unassigned", priority: "Medium",
  parent: "", fixVersion: "", affectsVersion: "",
  startDate: "", endDate: "", sprint: "",
  app_name: "", app_version: "", module: "", feature: "",
  test_name: "", steps_executed: [],
  issue_summary: "", ticket_id: "", internal_issue_id: "",
  created: false, rawPayload: null,
});

const formatIssueId = (id) => {
  if (!id) return "";
  if (String(id).startsWith("ISS-")) return String(id);
  const n = parseInt(id, 10);
  if (!isNaN(n)) return `ISS-${String(n).padStart(3, "0")}`;
  return String(id);
};

const mapPayloadToIssue = (payload) => {
  const jiraKey    = safeStr(pickFirst(payload, ["jira_key","jira_issue_key"]));
  const title      = safeStr(pickFirst(payload, ["title","issue_summary","summary"]));
  const desc       = safeStr(payload.description || "");
  const dev        = safeStr(pickFirst(payload, ["developer_name","developerName"])) || "Unassigned";
  const mod        = safeStr(payload.module || "");
  const jiraUrl    = safeStr(pickFirst(payload, ["jira_url","issue_url","browse_url","url"]));
  const priority   = safeStr(payload.priority || "High");
  const fixVersion = toArr(payload.fix_version ?? payload.fixVersion).join(", ");
  const affectsVer = toArr(payload.affects_version ?? payload.affectsVersion).join(", ");
  const startDate  = safeStr(payload.start_date || "");
  const endDate    = safeStr(payload.end_date   || "");
  const sprint     = safeStr(payload.sprint     || "Automation");

  return {
    ...emptyIssue(),
    source:            "draft",
    issueId:           jiraKey,
    jiraUrl,           title, description: desc,
    developer:         dev,
    parent:            safeStr(payload.parent || mod),
    fixVersion,        affectsVersion: affectsVer,
    startDate,         endDate, sprint, priority,
    app_name:          safeStr(payload.app_name),
    app_version:       safeStr(payload.app_version),
    module:            mod,
    feature:           safeStr(payload.feature),
    test_name:         safeStr(payload.test_name),
    steps_executed:    Array.isArray(payload.steps_executed) ? payload.steps_executed : [],
    issue_summary:     safeStr(payload.issue_summary) || title,
    ticket_id:         safeStr(payload.ticket_id),
    internal_issue_id: formatIssueId(safeStr(payload.issue_id)),  // → "ISS-001"
    created:           !!(jiraKey && jiraUrl),
    rawPayload:        payload,
  };
};

/* ── Dismiss a payload on the server (prevents re-show on refresh) ── */
const postDismiss = (payload) => {
  if (!payload) return;
  fetch(`${BACKEND}/api/jira/dismiss`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).catch(() => {});
};

/* ── sessionStorage helpers ── */
const ssLoad = () => {
  try {
    const raw = sessionStorage.getItem(SS_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
};
const ssSave = (issues) => {
  try { sessionStorage.setItem(SS_KEY, JSON.stringify(issues)); } catch {}
};
const ssClear = () => {
  try { sessionStorage.removeItem(SS_KEY); } catch {}
};

/* ─── Styles ──────────────────────────────────────────────────────────────── */
const S = {
  label: {
    fontSize:"0.73rem", fontWeight:600,
    color:"var(--text-secondary)", marginBottom:"3px", display:"block",
  },
  input: (locked) => ({
    width:"100%", boxSizing:"border-box",
    background: locked ? "var(--bg-console)" : "var(--input-bg)",
    border:"1px solid var(--border-color)",
    borderRadius:"6px", padding:"6px 10px",
    fontSize:"0.8rem",
    color: locked ? "var(--text-secondary)" : "var(--text-primary)",
    cursor: locked ? "not-allowed" : "text",
  }),
  btn: (color) => ({
    display:"inline-flex", alignItems:"center", gap:"5px",
    background:"none", border:`1.5px solid ${color}`,
    borderRadius:"6px", padding:"6px 16px",
    cursor:"pointer", fontSize:"0.8rem", color,
    fontWeight:700, textDecoration:"none", whiteSpace:"nowrap",
  }),
  badge: (bg, color) => ({
    fontSize:"0.67rem", fontWeight:800, flexShrink:0,
    background:bg, color, borderRadius:"4px", padding:"1px 6px",
  }),
};

/* ─── Component ───────────────────────────────────────────────────────────── */
export default function IssuePanel({
  modules         = [],
  jiraIssues      = [],
  onHistoryUpdate = null,
}) {
  // Restore issues from sessionStorage on mount (survives route changes)
  const [issues,        setIssues]        = useState(() => ssLoad() || []);
  const [expandedIdx,   setExpandedIdx]   = useState(null);
  const [isFullScreen,  setIsFullScreen]  = useState(false);
  const [creatingIdx,   setCreatingIdx]   = useState(null);
  const [errorMap,      setErrorMap]      = useState({});
  const [wsConnected,   setWsConnected]   = useState(false);
  const [serverReady,   setServerReady]   = useState(null);

  // importedKeys built from current issues on mount — prevents re-adding on refresh
  const importedKeys = useRef(new Set(
    (ssLoad() || []).map(iss => dedupKey(iss.rawPayload || iss))
  ));

  const setErr = (idx, msg) => setErrorMap((p) => ({ ...p, [idx]: msg || null }));

  // Persist issues to sessionStorage whenever they change
  useEffect(() => { ssSave(issues); }, [issues]);

  /* ── Server health ── */
  useEffect(() => {
    fetch(`${BACKEND}/api/health`)
      .then(r => r.json())
      .then(d => setServerReady(d.status === "ok"))
      .catch(() => setServerReady(false));
  }, []);

  /* ── Add payload (dedup by test_name+module) ── */
  const addPayload = useCallback((payload) => {
    if (!payload || typeof payload !== "object") return;
    const key = dedupKey(payload);
    if (importedKeys.current.has(key)) return;
    importedKeys.current.add(key);
    setIssues(prev => {
      const next = [...prev, mapPayloadToIssue(payload)];
      setExpandedIdx(next.length - 1);
      return next;
    });
  }, []);

  /* ── Fetch active (non-dismissed) payloads on mount ── */
  useEffect(() => {
    // If we already have issues from sessionStorage, skip fetch
    // This prevents duplicates when navigating back to this route
    const saved = ssLoad();
    if (saved && saved.length > 0) return;

    fetch(`${BACKEND}/api/jira/payloads`)
      .then(r => r.json())
      .then(d => { (d.payloads || []).forEach(addPayload); })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ── WebSocket ── */
  useEffect(() => {
    let ws, dead = false;
    const connect = () => {
      try {
        ws = new WebSocket(WS_BACKEND);
        ws.onopen  = () => setWsConnected(true);
        ws.onclose = () => { setWsConnected(false); if (!dead) setTimeout(connect, 3000); };
        ws.onerror = () => setWsConnected(false);
        ws.onmessage = (evt) => {
          try {
            const msg = JSON.parse(evt.data);

            // NEW RUN STARTED → clear everything
            if (msg.type === "RUN_START") {
              importedKeys.current = new Set();
              setIssues([]);
              ssClear();
              setExpandedIdx(null);
              setErrorMap({});
              return;
            }

            if (msg.type === "JIRA_PAYLOAD" && msg.payload) {
              addPayload(msg.payload);
              return;
            }
            if (msg.type === "LOG" && msg.payload?.message) {
              const p = parsePayloadFromLogLine(msg.payload.message);
              if (p) addPayload(p);
            }
          } catch (_) {}
        };
      } catch (_) { if (!dead) setTimeout(connect, 3000); }
    };
    connect();
    return () => { dead = true; try { ws?.close(); } catch (_) {} };
  }, [addPayload]);

  // Handle any jiraIssues passed as prop (legacy support)
  useEffect(() => {
    (Array.isArray(jiraIssues) ? jiraIssues : []).forEach(addPayload);
  }, [jiraIssues, addPayload]);

  const toggle   = (i) => { setExpandedIdx(p => p === i ? null : i); setErrorMap({}); };
  const addNew   = () => { setIssues(p => [...p, emptyIssue()]); setExpandedIdx(issues.length); };
  const setField = (i, f, v) => setIssues(p => p.map((x, j) => j === i ? { ...x, [f]: v } : x));

  /* ── Remove → JiraHistory Unassigned ── */
  const removeIssue = (idx) => {
    const iss = issues[idx];
    if (!iss) return;

    const entry = {
      type:              "removed",
      savedAt:           new Date().toLocaleString(),
      title:             iss.title             || iss.issue_summary || "Untitled",
      module:            iss.module            || iss.parent        || "",
      priority:          iss.priority          || "Medium",
      developer:         iss.developer         || "Unassigned",
      app_name:          iss.app_name          || "",
      app_version:       iss.app_version       || "",
      test_name:         iss.test_name         || "",
      issueId:           "",
      internal_issue_id: iss.internal_issue_id || "",
      ticket_id:         iss.ticket_id         || "",
      jiraUrl:           "",
    };

    if (typeof onHistoryUpdate === "function") onHistoryUpdate(entry);

    // Tell server to exclude from future /api/jira/payloads responses
    postDismiss(
      iss.rawPayload ||
      { test_name: iss.test_name, module: iss.module, issue_summary: iss.issue_summary }
    );

    setIssues(p => p.filter((_, i) => i !== idx));
    setExpandedIdx(p => p === idx ? null : p > idx ? p - 1 : p);
    setErrorMap({});
  };

  /* ── Create → JiraHistory Assigned ── */
  const createJira = async (idx) => {
    const iss = issues[idx];
    if (!iss) return;
    if (serverReady === false) { setErr(idx, "Old server.py running — restart backend"); return; }

    setCreatingIdx(idx);
    setErr(idx, null);

    try {
      const body = {
        app_name:        iss.app_name        || "",
        app_version:     iss.app_version     || "",
        module:          iss.module          || iss.parent || "",
        feature:         iss.feature         || "",
        issue_summary:   iss.issue_summary   || iss.title  || "",
        test_name:       iss.test_name       || "",
        steps_executed:  Array.isArray(iss.steps_executed) && iss.steps_executed.length
                           ? iss.steps_executed : [],
        developer_name:  iss.developer !== "Unassigned" ? iss.developer : "",
        title:           iss.title           || "",
        description:     iss.description     || "",
        parent:          iss.parent          || "",
        fix_version:     iss.fixVersion      ? iss.fixVersion.split(",").map(s => s.trim()).filter(Boolean) : [],
        affects_version: iss.affectsVersion  ? iss.affectsVersion.split(",").map(s => s.trim()).filter(Boolean) : [],
        priority:        iss.priority        || "High",
        ticket_id:       iss.ticket_id       || "",
        start_date:      iss.startDate       || "",
        end_date:        iss.endDate         || "",
        sprint:          iss.sprint          || "Automation",
      };

      const res = await fetch(`${BACKEND}/api/jira/create`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      let data = {};
      try { data = await res.json(); } catch (_) {}

      if (!res.ok) {
        if (res.status === 404) setServerReady(false);
        setErr(idx, data?.detail || `HTTP ${res.status} error`);
        return;
      }

      const issueKey = data.issue_id || data.issue_key || "";
      const jiraUrl  = data.issue_url || (issueKey ? `https://malothram70.atlassian.net/browse/${issueKey}` : "");

      // Dismiss from server
      postDismiss(
        iss.rawPayload ||
        { test_name: iss.test_name, module: iss.module, issue_summary: iss.issue_summary }
      );

      // Notify JiraHistory as Assigned
      if (typeof onHistoryUpdate === "function") {
        onHistoryUpdate({
          type:              "created",
          savedAt:           new Date().toLocaleString(),
          issueId:           issueKey,
          jiraUrl,
          title:             iss.title             || iss.issue_summary || "Untitled",
          module:            iss.module            || "",
          priority:          iss.priority          || "High",
          developer:         iss.developer         || "",
          app_name:          iss.app_name          || "",
          app_version:       iss.app_version       || "",
          test_name:         iss.test_name         || "",
          internal_issue_id: iss.internal_issue_id || "",
        });
      }

      // Remove from panel
      setIssues(p => p.filter((_, i) => i !== idx));
      setExpandedIdx(p => p === idx ? null : p > idx ? p - 1 : p);

    } catch (e) {
      setErr(idx, `Network error — is backend running? (${e?.message || e})`);
    } finally {
      setCreatingIdx(null);
    }
  };

  const draftCount  = issues.filter(i => i?.source === "draft").length;
  const manualCount = issues.filter(i => i?.source === "manual").length;

  /* ── Render ─────────────────────────────────────────────────────────────── */
  return (
    <div style={{
      display:"flex", flexDirection:"column",
      height: isFullScreen ? "100vh" : "350px",
      ...(isFullScreen
        ? { position:"fixed", top:0, left:0, width:"100vw", zIndex:9999, borderRadius:0 }
        : { borderRadius:"0.75rem" }),
      background:"var(--bg-card)", border:"1px solid var(--border-color)",
      overflow:"hidden", fontFamily:"'Courier New', Courier, monospace",
      boxShadow:"0 2px 4px rgba(15,23,42,.04), 0 8px 24px rgba(15,23,42,.08)",
    }}>

      {/* Old server warning */}
      {serverReady === false && (
        <div style={{ background:"#fef2f2", borderBottom:"1px solid #fecaca", padding:"6px 12px", fontSize:"0.71rem", color:"#b91c1c", flexShrink:0 }}>
          ⚠️ Old server detected — restart backend with new server.py
        </div>
      )}

      {/* Header */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"0.6rem 0.8rem", borderBottom:"1px solid var(--border-color)", background:"var(--bg-console)", flexShrink:0 }}>
        <div style={{ display:"flex", alignItems:"center", gap:"7px" }}>
          <AlertCircle size={14} color="var(--accent-blue)" />
          <span style={{ fontSize:"0.73rem", fontWeight:700, textTransform:"uppercase", letterSpacing:".05em", color:"var(--text-secondary)" }}>ISSUE LIST</span>
          <span title={wsConnected ? "Connected" : "Disconnected"}>
            {wsConnected ? <Wifi size={12} color="#16a34a" /> : <WifiOff size={12} color="#dc2626" />}
          </span>
          <span style={{ fontSize:"0.65rem", fontWeight:700, borderRadius:"4px", padding:"1px 5px", background: serverReady === true ? "#dcfce7" : serverReady === false ? "#fee2e2" : "#f1f5f9", color: serverReady === true ? "#16a34a" : serverReady === false ? "#dc2626" : "#64748b" }}>
            {serverReady === null ? "…" : serverReady ? "v2 ✓" : "OLD"}
          </span>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:"5px" }}>
          {[`${issues.length} total`, `${draftCount} auto`, `${manualCount} manual`].map(lbl => (
            <span key={lbl} style={{ fontSize:"0.67rem", color:"var(--text-secondary)", background:"var(--border-color)", borderRadius:"999px", padding:"2px 7px" }}>{lbl}</span>
          ))}
          <button onClick={addNew} style={{ display:"inline-flex", alignItems:"center", gap:"3px", background:"var(--accent-blue)", border:"none", borderRadius:"5px", padding:"3px 8px", cursor:"pointer", fontSize:"0.68rem", color:"#fff", fontWeight:600 }}>
            <Plus size={11} /> New
          </button>
          <button onClick={() => setIsFullScreen(f => !f)} style={{ background:"none", border:"none", cursor:"pointer", color:"#94a3b8", display:"flex", alignItems:"center", padding:"2px" }}>
            {isFullScreen ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          </button>
        </div>
      </div>

      {/* Accordion list */}
      <div style={{ flex:1, overflowY:"auto", padding:"8px", display:"flex", flexDirection:"column", gap:"5px" }}>

        {issues.length === 0 && (
          <div style={{ textAlign:"center", color:"var(--text-secondary)", fontSize:"0.78rem", padding:"24px 16px" }}>
            <div style={{ fontSize:"1.4rem", marginBottom:"6px" }}>🔍</div>
            {wsConnected
              ? "Waiting for test failures… issues appear here automatically."
              : "WebSocket disconnected — is backend running on port 8000?"}
            <div style={{ marginTop:"8px" }}>Or click <strong>+ New</strong> to add manually.</div>
          </div>
        )}

        {issues.map((iss, idx) => {
          const isOpen    = expandedIdx === idx;
          const pColor    = PRIORITY_COLOR[iss.priority] ?? "#64748b";
          const isCreated = !!iss.created || (!!iss.issueId && !!iss.jiraUrl);
          const canCreate = iss.source === "draft" && !isCreated;
          const spinning  = creatingIdx === idx;
          const locked    = isCreated;
          const errMsg    = errorMap[idx];
          const displayId = iss.internal_issue_id || (iss.issueId ? "" : `ISS-${String(idx + 1).padStart(3, "0")}`);

          return (
            <div key={idx} style={{ border:"1px solid var(--border-color)", borderLeft:`3px solid ${pColor}`, borderRadius:"7px", background:"var(--bg-card)", flexShrink:0 }}>

              {/* Row header */}
              <button onClick={() => toggle(idx)} style={{ width:"100%", display:"flex", alignItems:"center", gap:"7px", padding:"7px 9px", background: isOpen ? "var(--input-bg)" : "transparent", border:"none", cursor:"pointer", textAlign:"left", borderBottom: isOpen ? "1px solid var(--border-color)" : "none", borderRadius: isOpen ? "6px 6px 0 0" : "6px" }}>
                {isOpen ? <ChevronDown size={13} color="var(--text-secondary)" /> : <ChevronRight size={13} color="var(--text-secondary)" />}
                <span style={S.badge(iss.source === "draft" ? "#dbeafe" : "var(--border-color)", iss.source === "draft" ? "#1d4ed8" : "var(--text-secondary)")}>
                  {iss.source === "draft" ? "AUTO" : "MANUAL"}
                </span>
                {iss.module && <span style={S.badge("#ede9fe","#7c3aed")}>{iss.module}</span>}
                <span style={{ color:"var(--accent-blue)", fontWeight:700, fontSize:"0.78rem", flexShrink:0 }}>
                  {iss.issueId || displayId}
                </span>
                <span style={{ flex:1, fontSize:"0.78rem", color:"var(--text-primary)", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                  {iss.title || <em style={{ color:"var(--text-secondary)" }}>Untitled</em>}
                </span>
                {isCreated && <span style={S.badge("#dcfce7","#16a34a")}>✓ Created</span>}
                <span style={{ color:pColor, fontSize:"0.7rem", fontWeight:700, flexShrink:0 }}>{iss.priority}</span>
              </button>

              {/* Expanded body */}
              {isOpen && (
                <div style={{ padding:"12px 14px", display:"flex", flexDirection:"column", gap:"9px" }}>

                  {/* Jira Key + Title */}
                  <div style={{ display:"flex", gap:"8px" }}>
                    <div style={{ flex:"0 0 34%" }}>
                      <label style={S.label}>Jira Issue Key</label>
                      <input style={S.input(true)} value={iss.issueId} readOnly
                        placeholder={displayId} />
                    </div>
                    <div style={{ flex:1 }}>
                      <label style={S.label}>Title <span style={{ color:"#ef4444" }}>*</span></label>
                      <input style={S.input(locked)} value={iss.title} readOnly={locked}
                        placeholder="Issue title…"
                        onChange={e => !locked && setField(idx, "title", e.target.value)} />
                    </div>
                  </div>

                  {/* Error text */}
                  <div>
                    <label style={S.label}>Error <span style={{ color:"#ef4444" }}>*</span></label>
                    <textarea style={{ ...S.input(locked), resize:"vertical", minHeight:"300px", fontFamily:"inherit", fontSize:"0.72rem", lineHeight:"1.5" }}
                      value={iss.description} readOnly={locked}
                      onChange={e => !locked && setField(idx, "description", e.target.value)} />
                  </div>

                  {/* Developer + Priority */}
                  <div style={{ display:"flex", gap:"8px" }}>
                    <div style={{ flex:1 }}>
                      <label style={S.label}>Developer</label>
                      {locked
                        ? <input style={S.input(true)} value={iss.developer} readOnly />
                        : <select style={S.input(false)} value={iss.developer} onChange={e => setField(idx, "developer", e.target.value)}>
                            {!DEVELOPERS.includes(iss.developer) && iss.developer !== "Unassigned" && <option value={iss.developer}>{iss.developer}</option>}
                            {DEVELOPERS.map(d => <option key={d}>{d}</option>)}
                          </select>
                      }
                    </div>
                    <div style={{ flex:1 }}>
                      <label style={S.label}>Priority</label>
                      {locked
                        ? <input style={S.input(true)} value={iss.priority} readOnly />
                        : <select style={S.input(false)} value={iss.priority} onChange={e => setField(idx, "priority", e.target.value)}>
                            {PRIORITIES.map(p => <option key={p}>{p}</option>)}
                          </select>
                      }
                    </div>
                  </div>

                  {/* Parent + Sprint */}
                  <div style={{ display:"flex", gap:"8px" }}>
                    <div style={{ flex:1 }}>
                      <label style={S.label}>Parent (Module)</label>
                      <input style={S.input(locked)} value={iss.parent} readOnly={locked}
                        onChange={e => !locked && setField(idx, "parent", e.target.value)} />
                    </div>
                    <div style={{ flex:1 }}>
                      <label style={S.label}>Sprint</label>
                      <input style={S.input(locked)} value={iss.sprint} readOnly={locked}
                        onChange={e => !locked && setField(idx, "sprint", e.target.value)} />
                    </div>
                  </div>

                  {/* Fix Version + Affects Version */}
                  <div style={{ display:"flex", gap:"8px" }}>
                    <div style={{ flex:1 }}>
                      <label style={S.label}>Fix Version</label>
                      <input style={S.input(locked)} value={iss.fixVersion} readOnly={locked}
                        placeholder="e.g. Production"
                        onChange={e => !locked && setField(idx, "fixVersion", e.target.value)} />
                    </div>
                    <div style={{ flex:1 }}>
                      <label style={S.label}>Affects Version</label>
                      <input style={S.input(locked)} value={iss.affectsVersion} readOnly={locked}
                        onChange={e => !locked && setField(idx, "affectsVersion", e.target.value)} />
                    </div>
                  </div>

                  {/* Start Date + End Date */}
                  <div style={{ display:"flex", gap:"8px" }}>
                    <div style={{ flex:1 }}>
                      <label style={S.label}>Start Date</label>
                      <input type="date" style={S.input(locked)} value={iss.startDate} readOnly={locked}
                        onChange={e => !locked && setField(idx, "startDate", e.target.value)} />
                    </div>
                    <div style={{ flex:1 }}>
                      <label style={S.label}>End Date (Due)</label>
                      <input type="date" style={S.input(locked)} value={iss.endDate} readOnly={locked}
                        onChange={e => !locked && setField(idx, "endDate", e.target.value)} />
                    </div>
                  </div>

                  {/* Jira link */}
                  {iss.jiraUrl && (
                    <div style={{ fontSize:"0.72rem", color:"var(--text-secondary)", display:"flex", alignItems:"center", gap:"6px" }}>
                      <span>Jira:</span>
                      <a href={iss.jiraUrl} target="_blank" rel="noreferrer" style={{ color:"var(--accent-blue)", fontWeight:700, textDecoration:"none" }}>{iss.issueId} ↗</a>
                    </div>
                  )}

                  {/* Error banner */}
                  {errMsg && (
                    <div style={{ background:"#fef2f2", border:"1px solid #fecaca", borderRadius:"6px", padding:"9px 12px", fontSize:"0.73rem", color:"#b91c1c", lineHeight:"1.7" }}>
                      <strong>⚠️ Create failed:</strong><br />
                      {errMsg.split("\n").map((l, i) => <div key={i}>{l}</div>)}
                      <div style={{ marginTop:"6px" }}>
                        Diagnose: <a href={`${BACKEND}/api/jira/test-connection`} target="_blank" rel="noreferrer" style={{ color:"#b91c1c", fontWeight:700 }}>/api/jira/test-connection ↗</a>
                      </div>
                    </div>
                  )}

                  {/* Action buttons */}
                  <div style={{ display:"flex", justifyContent:"flex-end", alignItems:"center", gap:"10px", paddingBottom:"4px", flexWrap:"wrap" }}>
                    {/* Remove only before creation */}
                    {!isCreated && (
                      <button onClick={() => removeIssue(idx)} style={S.btn("#ef4444")}>✕ Remove</button>
                    )}
                    {/* Open in Jira after creation */}
                    {isCreated && iss.jiraUrl && (
                      <a href={iss.jiraUrl} target="_blank" rel="noreferrer" style={S.btn("#16a34a")}>
                        <ExternalLink size={13} /> Open in Jira
                      </a>
                    )}
                    {/* Create button */}
                    {canCreate && (
                      <button
                        onClick={() => createJira(idx)}
                        disabled={!iss.title.trim() || !iss.description.trim() || spinning}
                        className="run-button"
                        style={{
                          padding:"6px 24px", fontSize:"0.82rem", minWidth:"100px",
                          opacity: (!iss.title.trim() || !iss.description.trim()) ? 0.4 : 1,
                          cursor: (!iss.title.trim() || !iss.description.trim() || spinning) ? "not-allowed" : "pointer",
                        }}
                      >
                        {spinning ? "Creating…" : "Create"}
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