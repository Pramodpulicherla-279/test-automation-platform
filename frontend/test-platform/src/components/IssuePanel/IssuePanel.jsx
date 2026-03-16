/**
 * IssuePanel.jsx
 *
 * Flow:
 *  1. On mount → GET /api/health to check if new server is running
 *     If 404 → shows banner "Old server running — restart backend"
 *  2. Test fails → conftest POSTs to /api/jira/payload → JIRA_PAYLOAD broadcast
 *  3. IssuePanel receives → auto-populates accordion row
 *  4. User clicks "Create" → POST /api/jira/create
 *  5. Success → "Open in Jira" button appears, saved to History "Assigned"
 *  6. "Remove" → saved to History "Unassigned"
 */

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  AlertCircle, ChevronDown, ChevronRight,
  ExternalLink, Maximize2, Minimize2, Plus, Trash2, Wifi, WifiOff,
} from "lucide-react";

const BACKEND    = "http://localhost:8000";
const WS_BACKEND = "ws://localhost:8000/ws/test-status";

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

const dedupKey = (p) => {
  const tid = safeStr(p?.test_id || p?.testId).trim();
  if (tid) return `tid::${tid}`;
  const iid = safeStr(p?.issue_id || p?.issueId).trim();
  if (iid) return `iid::${iid}`;
  return `sum::${safeStr(p?.module)}::${safeStr(p?.issue_summary || p?.title)}`;
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

const getFixVersionText = (p) => {
  const v = p?.fix_version ?? p?.fixVersion ?? [];
  if (Array.isArray(v)) return v.filter(Boolean).map(String).join(", ");
  return safeStr(v);
};

const emptyIssue = () => ({
  source: "manual",
  jiraUrl: "", issueId: "", title: "", description: "",
  developer: "Unassigned", priority: "Medium",
  parent: "", fixVersion: "", testId: "",
  app_name: "", app_version: "", module: "", feature: "",
  test_name: "", test_id: "", steps_executed: [],
  issue_summary: "", ticket_id: "", internal_issue_id: "",
  created: false, rawPayload: null,
});

const mapPayloadToIssue = (payload, modules = []) => {
  const jiraKey  = safeStr(pickFirst(payload, ["jira_key", "jira_issue_key"]));
  const title    = safeStr(pickFirst(payload, ["title", "issue_summary", "summary"]));
  const desc     = safeStr(payload.description || "");
  const dev      = safeStr(pickFirst(payload, ["developer_name", "developerName"])) || "Unassigned";
  const mod      = safeStr(payload.module || "");
  const parent   = safeStr(payload.parent || mod);
  const fixVer   = safeStr(getFixVersionText(payload));
  const jiraUrl  = safeStr(pickFirst(payload, ["jira_url", "issue_url", "browse_url", "url"]));
  const priority = safeStr(payload.priority || "High");
  const testId   = mod && (modules || []).some(
    (m) => (m?.name || "").toLowerCase() === mod.toLowerCase()
  ) ? mod : "";

  return {
    ...emptyIssue(),
    source: "draft",
    issueId: jiraKey, jiraUrl, title, description: desc,
    developer: dev, parent, fixVersion: fixVer, testId, priority,
    app_name:          safeStr(payload.app_name),
    app_version:       safeStr(payload.app_version),
    module:            mod,
    feature:           safeStr(payload.feature),
    test_name:         safeStr(payload.test_name),
    test_id:           safeStr(payload.test_id),
    steps_executed:    Array.isArray(payload.steps_executed) ? payload.steps_executed : [],
    issue_summary:     safeStr(payload.issue_summary) || title,
    ticket_id:         safeStr(payload.ticket_id),
    internal_issue_id: safeStr(payload.issue_id),
    created:           !!(jiraKey && jiraUrl),
    rawPayload:        payload,
  };
};

/* ─── Style tokens ────────────────────────────────────────────────────────── */
const S = {
  label: {
    fontSize: "0.73rem", fontWeight: 600,
    color: "var(--text-secondary)", marginBottom: "3px", display: "block",
  },
  input: {
    width: "100%", boxSizing: "border-box",
    background: "var(--input-bg)", border: "1px solid var(--border-color)",
    borderRadius: "6px", padding: "6px 10px",
    fontSize: "0.8rem", color: "var(--text-primary)",
  },
  btn: (color) => ({
    display: "inline-flex", alignItems: "center", gap: "5px",
    background: "none", border: `1.5px solid ${color}`,
    borderRadius: "6px", padding: "6px 16px",
    cursor: "pointer", fontSize: "0.8rem", color,
    fontWeight: 700, textDecoration: "none", whiteSpace: "nowrap",
  }),
  badge: (bg, color) => ({
    fontSize: "0.67rem", fontWeight: 800, flexShrink: 0,
    background: bg, color, borderRadius: "4px", padding: "1px 6px",
  }),
};

/* ─── Component ───────────────────────────────────────────────────────────── */
export default function IssuePanel({ modules = [], jiraIssues = [] }) {
  const [issues,        setIssues]        = useState([]);
  const [history,       setHistory]       = useState([]);
  const [expandedIdx,   setExpandedIdx]   = useState(null);
  const [isFullScreen,  setIsFullScreen]  = useState(false);
  const [showHistory,   setShowHistory]   = useState(false);
  const [historyTab,    setHistoryTab]    = useState("created");
  const [creatingIdx,   setCreatingIdx]   = useState(null);
  const [errorMap,      setErrorMap]      = useState({});
  const [wsConnected,   setWsConnected]   = useState(false);
  const [totalReceived, setTotalReceived] = useState(0);
  // Server version check — null=checking, true=ok, false=old server
  const [serverReady,   setServerReady]   = useState(null);
  const [jiraConfig,    setJiraConfig]    = useState(null);

  const importedKeys = useRef(new Set());

  const setErr = (idx, msg) =>
    setErrorMap((p) => ({ ...p, [idx]: msg || null }));

  /* ── Check if new server is running ── */
  useEffect(() => {
    fetch(`${BACKEND}/api/health`)
      .then((r) => r.json())
      .then((d) => {
        if (d.status === "ok") {
          setServerReady(true);
          setJiraConfig(d);
        } else {
          setServerReady(false);
        }
      })
      .catch(() => setServerReady(false));
  }, []);

  /* ── Add payload (dedup) ── */
  const addPayload = useCallback((payload) => {
    if (!payload || typeof payload !== "object") return;
    const key = dedupKey(payload);
    if (importedKeys.current.has(key)) return;
    importedKeys.current.add(key);
    setTotalReceived((n) => n + 1);
    setIssues((prev) => {
      const next = [...prev, mapPayloadToIssue(payload, modules)];
      setExpandedIdx(next.length - 1);
      return next;
    });
  }, [modules]);

  /* ── Fetch missed payloads on mount ── */
  useEffect(() => {
    fetch(`${BACKEND}/api/jira/payloads`)
      .then((r) => r.json())
      .then((d) => { (d.payloads || []).forEach(addPayload); })
      .catch(() => {});
  }, [addPayload]);

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
            if (msg.type === "JIRA_PAYLOAD" && msg.payload) { addPayload(msg.payload); return; }
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

  /* ── Legacy prop ── */
  useEffect(() => {
    (Array.isArray(jiraIssues) ? jiraIssues : []).forEach(addPayload);
  }, [jiraIssues, addPayload]);

  const toggle   = (i) => { setExpandedIdx((p) => (p === i ? null : i)); setErrorMap({}); };
  const addNew   = () => { setIssues((p) => [...p, emptyIssue()]); setExpandedIdx(issues.length); };
  const setField = (i, f, v) =>
    setIssues((p) => p.map((x, j) => j === i ? { ...x, [f]: v } : x));

  const removeIssue = (idx) => {
    setHistory((p) => [{ ...issues[idx], type: "removed", savedAt: new Date().toLocaleString() }, ...p]);
    setIssues((p) => p.filter((_, i) => i !== idx));
    setExpandedIdx((p) => p === idx ? null : p > idx ? p - 1 : p);
    setErrorMap({});
  };

  /* ── Create Jira ticket ── */
  const createJira = async (idx) => {
    const iss = issues[idx];
    if (!iss) return;

    // Block if old server is running
    if (serverReady === false) {
      setErr(idx,
        "Old server.py is running — it does not have the /api/jira/create route.\n" +
        "Fix: Stop backend (Ctrl+C), replace backend/server.py with the new file, restart with: python server.py\n" +
        "Then verify at: http://localhost:8000/api/health"
      );
      return;
    }

    setCreatingIdx(idx);
    setErr(idx, null);

    try {
      const body = {
        app_name:       iss.app_name       || "",
        app_version:    iss.app_version    || "",
        module:         iss.module         || iss.parent || "",
        feature:        iss.feature        || "",
        issue_summary:  iss.issue_summary  || iss.title  || "",
        test_name:      iss.test_name      || "",
        test_id:        iss.test_id        || "",
        steps_executed: Array.isArray(iss.steps_executed) && iss.steps_executed.length
                          ? iss.steps_executed : [],
        developer_name: iss.developer !== "Unassigned" ? iss.developer : "",
        title:          iss.title       || "",
        description:    iss.description || "",
        parent:         iss.parent      || "",
        fix_version:    iss.fixVersion  ? [iss.fixVersion] : [],
        priority:       iss.priority    || "High",
        ticket_id:      iss.ticket_id   || "",
      };

      const res = await fetch(`${BACKEND}/api/jira/create`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
      });

      let data = {};
      try { data = await res.json(); } catch (_) {}

      if (!res.ok) {
        // 404 = old server still running
        if (res.status === 404) {
          setServerReady(false);
          setErr(idx,
            "404 Not Found — the old server.py is still running.\n" +
            "Steps to fix:\n" +
            "1. Stop backend (Ctrl+C in terminal)\n" +
            "2. Replace backend/server.py with the new version\n" +
            "3. Run: python server.py\n" +
            "4. Check: http://localhost:8000/api/health"
          );
        } else {
          setErr(idx, data?.detail || `HTTP ${res.status} error`);
        }
        return;
      }

      const issueKey = data.issue_id || data.issue_key || "";
      const jiraUrl  = data.issue_url || (issueKey ? `${BACKEND}/browse/${issueKey}` : "");
      const updated  = { ...iss, issueId: issueKey, jiraUrl, created: true };

      setIssues((p) => p.map((x, i) => i === idx ? updated : x));
      setHistory((p) => [{ ...updated, type: "created", savedAt: new Date().toLocaleString() }, ...p]);
      setErr(idx, null);

      // Refresh server health to get latest jira config
      fetch(`${BACKEND}/api/health`)
        .then((r) => r.json())
        .then((d) => { if (d.status === "ok") setJiraConfig(d); })
        .catch(() => {});

    } catch (e) {
      setErr(idx, `Network error — is backend running? (${e?.message || e})`);
    } finally {
      setCreatingIdx(null);
    }
  };

  const draftCount   = issues.filter((i) => i?.source === "draft").length;
  const manualCount  = issues.filter((i) => i?.source === "manual").length;
  const assignedHist = history.filter((h) => h.type === "created");
  const removedHist  = history.filter((h) => h.type === "removed");

  /* ────────────────────────────────────────────────────────────────────────── */
  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: isFullScreen ? "100vh" : "350px",
      ...(isFullScreen
        ? { position: "fixed", top: 0, left: 0, width: "100vw", zIndex: 9999, borderRadius: 0 }
        : { borderRadius: "0.75rem" }),
      background: "var(--bg-card)",
      border: "1px solid var(--border-color)",
      overflow: "hidden",
      fontFamily: "'Courier New', Courier, monospace",
      boxShadow: "0 2px 4px rgba(15,23,42,.04), 0 8px 24px rgba(15,23,42,.08)",
    }}>

      {/* ── Old server warning banner ── */}
      {serverReady === false && (
        <div style={{
          background: "#fef2f2", borderBottom: "1px solid #fecaca",
          padding: "8px 12px", fontSize: "0.72rem", color: "#b91c1c",
          flexShrink: 0, lineHeight: "1.6",
        }}>
          <strong>⚠️ Old server.py detected</strong> — /api/jira/create route is missing.<br />
          Stop backend → replace <code>backend/server.py</code> → restart → verify at{" "}
          <a href={`${BACKEND}/api/health`} target="_blank" rel="noreferrer"
            style={{ color: "#b91c1c", fontWeight: 700 }}>
            /api/health
          </a>
        </div>
      )}

      {/* ── Jira config warning (token not set) ── */}
      {serverReady === true && jiraConfig && !jiraConfig.jira_token_set && (
        <div style={{
          background: "#fffbeb", borderBottom: "1px solid #fde68a",
          padding: "8px 12px", fontSize: "0.72rem", color: "#92400e",
          flexShrink: 0, lineHeight: "1.6",
        }}>
          <strong>⚠️ Jira not configured</strong> — JIRA_API_TOKEN not set in backend/.env<br />
          Also check: JIRA_URL={jiraConfig.jira_url} · PROJECT={jiraConfig.jira_project_key} · EMAIL={jiraConfig.jira_email}
        </div>
      )}

      {/* ── Header ── */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "0.65rem 0.8rem", borderBottom: "1px solid var(--border-color)",
        background: "var(--bg-console)", flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
          <AlertCircle size={14} color="var(--accent-blue)" />
          <span style={{ fontSize: "0.73rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".05em", color: "var(--text-secondary)" }}>
            ISSUE LIST
          </span>
          <span title={wsConnected ? "WebSocket connected" : "Disconnected"}>
            {wsConnected ? <Wifi size={12} color="#16a34a" /> : <WifiOff size={12} color="#dc2626" />}
          </span>
          {/* Server version indicator */}
          <span title={
            serverReady === null ? "Checking server..." :
            serverReady ? "New server.py running ✓" :
            "Old server.py — restart backend!"
          } style={{
            fontSize: "0.65rem", fontWeight: 700, borderRadius: "4px", padding: "1px 5px",
            background: serverReady === true ? "#dcfce7" : serverReady === false ? "#fee2e2" : "#f1f5f9",
            color:      serverReady === true ? "#16a34a" : serverReady === false ? "#dc2626" : "#64748b",
          }}>
            {serverReady === null ? "…" : serverReady ? "v2 ✓" : "OLD SERVER"}
          </span>
          {totalReceived > 0 && (
            <span style={{ fontSize: "0.67rem", fontWeight: 800, background: "#dbeafe", color: "#1d4ed8", borderRadius: "999px", padding: "1px 7px" }}>
              {totalReceived} received
            </span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          {[`${issues.length} total`, `${draftCount} auto`, `${manualCount} manual`].map((lbl) => (
            <span key={lbl} style={{ fontSize: "0.68rem", color: "var(--text-secondary)", background: "var(--border-color)", borderRadius: "999px", padding: "2px 7px" }}>
              {lbl}
            </span>
          ))}
          <button onClick={() => setShowHistory((f) => !f)} style={{
            fontSize: "0.68rem", fontWeight: 600, border: "none",
            borderRadius: "5px", padding: "3px 8px", cursor: "pointer",
            background: showHistory ? "var(--accent-blue)" : "var(--border-color)",
            color: showHistory ? "#fff" : "var(--text-secondary)",
          }}>
            History {history.length > 0 && `(${history.length})`}
          </button>
          <button onClick={addNew} style={{
            display: "inline-flex", alignItems: "center", gap: "3px",
            background: "var(--accent-blue)", border: "none", borderRadius: "5px",
            padding: "3px 8px", cursor: "pointer", fontSize: "0.68rem", color: "#fff", fontWeight: 600,
          }}>
            <Plus size={11} /> New
          </button>
          <button onClick={() => setIsFullScreen((f) => !f)} style={{
            background: "none", border: "none", cursor: "pointer",
            color: "#94a3b8", display: "flex", alignItems: "center", padding: "2px",
          }}>
            {isFullScreen ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          </button>
        </div>
      </div>

      {/* ── History ── */}
      {showHistory && (
        <div style={{ borderBottom: "1px solid var(--border-color)", background: "var(--bg-console)", padding: "8px 12px", flexShrink: 0 }}>
          <div style={{ display: "flex", gap: "5px", marginBottom: "7px" }}>
            {[
              { key: "created", label: `Assigned (${assignedHist.length})` },
              { key: "removed", label: `Unassigned (${removedHist.length})` },
            ].map((tab) => (
              <button key={tab.key} onClick={() => setHistoryTab(tab.key)} style={{
                padding: "3px 10px", borderRadius: "999px",
                border: "1px solid var(--border-color)", cursor: "pointer",
                fontSize: "0.68rem", fontWeight: historyTab === tab.key ? 700 : 400,
                background: historyTab === tab.key ? "var(--accent-blue)" : "transparent",
                color: historyTab === tab.key ? "#fff" : "var(--text-secondary)",
              }}>
                {tab.label}
              </button>
            ))}
          </div>
          {(() => {
            const list = historyTab === "created" ? assignedHist : removedHist;
            if (!list.length) return (
              <div style={{ fontSize: "0.73rem", color: "var(--text-secondary)", padding: "5px 0" }}>
                No {historyTab === "created" ? "assigned" : "removed"} issues yet.
              </div>
            );
            return (
              <div style={{ display: "flex", flexDirection: "column", gap: "4px", maxHeight: "140px", overflowY: "auto" }}>
                {list.map((h, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: "6px", background: "var(--bg-card)", borderRadius: "5px", border: "1px solid var(--border-color)", padding: "5px 9px" }}>
                    <span style={S.badge(
                      historyTab === "created" ? "#dcfce7" : "#fee2e2",
                      historyTab === "created" ? "#16a34a" : "#dc2626",
                    )}>
                      {historyTab === "created" ? "ASSIGNED" : "REMOVED"}
                    </span>
                    <span style={{ color: "var(--accent-blue)", fontWeight: 700, fontSize: "0.73rem", flexShrink: 0 }}>
                      {h.issueId || h.internal_issue_id || "—"}
                    </span>
                    {h.module && <span style={S.badge("#ede9fe", "#7c3aed")}>{h.module}</span>}
                    <span style={{ flex: 1, fontSize: "0.73rem", color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {h.title || "Untitled"}
                    </span>
                    <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)", flexShrink: 0 }}>{h.savedAt}</span>
                    {historyTab === "created" && h.jiraUrl && (
                      <a href={h.jiraUrl} target="_blank" rel="noreferrer"
                        style={{ display: "flex", alignItems: "center", gap: "3px", color: "var(--accent-blue)", fontSize: "0.68rem", fontWeight: 700, textDecoration: "none", flexShrink: 0 }}>
                        <ExternalLink size={10} /> Open
                      </a>
                    )}
                  </div>
                ))}
              </div>
            );
          })()}
        </div>
      )}

      {/* ── Accordion list ── */}
      <div style={{ flex: 1, overflowY: "auto", padding: "8px", display: "flex", flexDirection: "column", gap: "5px" }}>

        {issues.length === 0 && (
          <div style={{ textAlign: "center", color: "var(--text-secondary)", fontSize: "0.78rem", padding: "24px 16px" }}>
            <div style={{ fontSize: "1.4rem", marginBottom: "6px" }}>🔍</div>
            {wsConnected
              ? "Waiting for test failures… issues appear here automatically."
              : "WebSocket disconnected — is backend running on port 8000?"}
            <div style={{ marginTop: "8px" }}>Or click <strong>+ New</strong> to add manually.</div>
          </div>
        )}

        {issues.map((iss, idx) => {
          const isOpen    = expandedIdx === idx;
          const pColor    = PRIORITY_COLOR[iss.priority] ?? "#64748b";
          const isCreated = !!iss.created || (iss.source === "draft" && !!iss.issueId && !!iss.jiraUrl);
          const spinning  = creatingIdx === idx;
          const canCreate = iss.source === "draft" && !isCreated;
          const errMsg    = errorMap[idx];

          return (
            <div key={idx} style={{
              border: "1px solid var(--border-color)",
              borderLeft: `3px solid ${pColor}`,
              borderRadius: "7px", background: "var(--bg-card)", flexShrink: 0,
            }}>

              {/* Row header */}
              <button onClick={() => toggle(idx)} style={{
                width: "100%", display: "flex", alignItems: "center", gap: "7px",
                padding: "7px 9px",
                background: isOpen ? "var(--input-bg)" : "transparent",
                border: "none", cursor: "pointer", textAlign: "left",
                borderBottom: isOpen ? "1px solid var(--border-color)" : "none",
                borderRadius: isOpen ? "6px 6px 0 0" : "6px",
              }}>
                {isOpen ? <ChevronDown size={13} color="var(--text-secondary)" /> : <ChevronRight size={13} color="var(--text-secondary)" />}
                <span style={S.badge(iss.source === "draft" ? "#dbeafe" : "var(--border-color)", iss.source === "draft" ? "#1d4ed8" : "var(--text-secondary)")}>
                  {iss.source === "draft" ? "AUTO" : "MANUAL"}
                </span>
                {iss.module && <span style={S.badge("#ede9fe", "#7c3aed")}>{iss.module}</span>}
                <span style={{ color: "var(--accent-blue)", fontWeight: 700, fontSize: "0.78rem", flexShrink: 0 }}>
                  {iss.issueId || iss.internal_issue_id || `#${idx + 1}`}
                </span>
                <span style={{ flex: 1, fontSize: "0.78rem", color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {iss.title || <em style={{ color: "var(--text-secondary)" }}>Untitled</em>}
                </span>
                {isCreated && <span style={S.badge("#dcfce7", "#16a34a")}>✓ Created</span>}
                <span style={{ color: pColor, fontSize: "0.7rem", fontWeight: 700, flexShrink: 0 }}>{iss.priority}</span>
              </button>

              {/* Body */}
              {isOpen && (
                <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: "9px" }}>

                  {/* Test ID */}
                  <div>
                    <label style={S.label}>Test ID</label>
                    <select style={S.input} value={iss.testId} onChange={(e) => setField(idx, "testId", e.target.value)}>
                      <option value="">-- Select Test --</option>
                      {(modules || []).map((m, i) => <option key={i} value={m.name}>{m.name} ({m.status})</option>)}
                    </select>
                  </div>

                  {/* Jira Key + Title */}
                  <div style={{ display: "flex", gap: "8px" }}>
                    <div style={{ flex: "0 0 34%" }}>
                      <label style={S.label}>Jira Issue Key</label>
                      <input style={{ ...S.input, color: "var(--text-secondary)", fontSize: "0.73rem" }}
                        value={iss.issueId} readOnly
                        placeholder={iss.internal_issue_id || "Assigned after Create"} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={S.label}>Title <span style={{ color: "#ef4444" }}>*</span></label>
                      <input style={S.input} placeholder="Issue title…" value={iss.title}
                        onChange={(e) => setField(idx, "title", e.target.value)} />
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <label style={S.label}>Description <span style={{ color: "#ef4444" }}>*</span></label>
                    <textarea
                      style={{ ...S.input, resize: "vertical", minHeight: "300px", fontFamily: "inherit", fontSize: "0.72rem", lineHeight: "1.5" }}
                      value={iss.description}
                      onChange={(e) => setField(idx, "description", e.target.value)}
                    />
                  </div>

                  {/* Developer + Priority */}
                  <div style={{ display: "flex", gap: "8px" }}>
                    <div style={{ flex: 1 }}>
                      <label style={S.label}>Developer</label>
                      <select style={S.input} value={iss.developer} onChange={(e) => setField(idx, "developer", e.target.value)}>
                        {!DEVELOPERS.includes(iss.developer) && iss.developer !== "Unassigned" && (
                          <option value={iss.developer}>{iss.developer}</option>
                        )}
                        {DEVELOPERS.map((d) => <option key={d}>{d}</option>)}
                      </select>
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={S.label}>Priority</label>
                      <select style={S.input} value={iss.priority} onChange={(e) => setField(idx, "priority", e.target.value)}>
                        {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
                      </select>
                    </div>
                  </div>

                  {/* Parent + Fix Version */}
                  <div style={{ display: "flex", gap: "8px" }}>
                    <div style={{ flex: 1 }}>
                      <label style={S.label}>Parent</label>
                      <input style={S.input} value={iss.parent} onChange={(e) => setField(idx, "parent", e.target.value)} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={S.label}>Fix Version</label>
                      <input style={S.input} value={iss.fixVersion} onChange={(e) => setField(idx, "fixVersion", e.target.value)} />
                    </div>
                  </div>

                  {/* Jira URL after creation */}
                  {iss.jiraUrl && (
                    <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "6px" }}>
                      <span>Jira ticket:</span>
                      <a href={iss.jiraUrl} target="_blank" rel="noreferrer"
                        style={{ color: "var(--accent-blue)", fontWeight: 700, textDecoration: "none" }}>
                        {iss.issueId} ↗
                      </a>
                    </div>
                  )}

                  {/* Error banner */}
                  {errMsg && (
                    <div style={{
                      background: "#fef2f2", border: "1px solid #fecaca",
                      borderRadius: "6px", padding: "10px 14px",
                      fontSize: "0.73rem", color: "#b91c1c", lineHeight: "1.8",
                    }}>
                      <div style={{ fontWeight: 700, marginBottom: "4px" }}>⚠️ Create failed</div>
                      {errMsg.split("\n").map((line, i) => (
                        <div key={i} style={{ marginBottom: "1px" }}>{line}</div>
                      ))}
                      <div style={{ marginTop: "8px", paddingTop: "8px", borderTop: "1px solid #fecaca" }}>
                        <strong>Diagnose:</strong>{" "}
                        <a href="http://localhost:8000/api/jira/test-connection" target="_blank" rel="noreferrer"
                          style={{ color: "#b91c1c", fontWeight: 700 }}>
                          http://localhost:8000/api/jira/test-connection ↗
                        </a>
                        {" "}— opens a page showing exactly what's wrong with your Jira config
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: "10px", paddingBottom: "4px", flexWrap: "wrap" }}>

                    <button onClick={() => removeIssue(idx)} style={S.btn("#ef4444")}>
                      <Trash2 size={13} /> Remove
                    </button>

                    {isCreated && iss.jiraUrl && (
                      <a href={iss.jiraUrl} target="_blank" rel="noreferrer" style={S.btn("#16a34a")}>
                        <ExternalLink size={13} /> Open in Jira
                      </a>
                    )}

                    {canCreate && (
                      <button
                        onClick={() => createJira(idx)}
                        disabled={!iss.title.trim() || !iss.description.trim() || spinning}
                        className="run-button"
                        style={{
                          padding: "6px 24px", fontSize: "0.82rem", minWidth: "100px",
                          opacity: (!iss.title.trim() || !iss.description.trim()) ? 0.4 : 1,
                          cursor: (!iss.title.trim() || !iss.description.trim() || spinning) ? "not-allowed" : "pointer",
                        }}
                        title={!iss.title.trim() || !iss.description.trim() ? "Title and Description required" : `Create: ${iss.title}`}
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