/**
 * IssuePanel.jsx
 *
 * Structure: Issues grouped by ticket_id (Run ID).
 *
 *  ▼ RUN-20260317-184809   ← parent accordion (one per test run)
 *      ▼ ISS-001  Login — test_login_success       ← child accordion
 *      ▼ ISS-002  Onboarding — test_onboarding_success
 *      ▼ ISS-003  Onboarding — test_addfarm_addcrop_success
 *
 * Each child shows: Title, Error, Developer, Priority, Parent, Sprint,
 *                   Fix Version, Affects Version, Start Date, End Date.
 * Remove/Create buttons per child.
 * Issues persisted in sessionStorage — survive route navigation.
 * Cleared on new test run (RUN_START WebSocket message).
 */

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  AlertCircle, ChevronDown, ChevronRight,
  ExternalLink, Maximize2, Minimize2, Wifi, WifiOff,
  FolderOpen, Folder,
} from "lucide-react";

const BACKEND = "http://localhost:8000";
const WS_BACKEND = "ws://localhost:8000/ws/test-status";
const SS_KEY = "issuePanelIssues";

const DEVELOPERS = ["Unassigned", "Ram", "Anuj", "Vaibhav", "Vikash", "Swaroopa", "Krishivaas"];
const PRIORITIES = ["High", "Medium", "Low"];
const PRIORITY_COLOR = { High: "#dc2626", Medium: "#d97706", Low: "#64748b" };

/* ─── Helpers ─────────────────────────────────────────────────────────────── */
const safeStr = (v) => (v == null ? "" : String(v));
const pickFirst = (obj, keys) => {
  for (const k of keys) { const v = obj?.[k]; if (v != null && String(v).trim()) return v; }
  return "";
};
const dedupKey = (p) => {
  const tn = safeStr(p?.test_name || "").trim();
  const md = safeStr(p?.module || "").trim();
  if (tn) return `tn::${md}::${tn}`;
  return `sum::${md}::${safeStr(p?.issue_summary || p?.title || "").trim()}`;
};
const parsePayloadFromLogLine = (line) => {
  for (const prefix of ["JIRA_PAYLOAD_JSON:", "AUTOMATION_PAYLOAD_JSON:"]) {
    if (typeof line === "string" && line.startsWith(prefix)) {
      try { return JSON.parse(line.slice(prefix.length).trim()); } catch (_) { }
    }
  }
  return null;
};
const toArr = (v) => {
  if (!v) return [];
  if (Array.isArray(v)) return v.filter(Boolean).map(String);
  return [String(v)].filter(Boolean);
};
const formatIssueId = (id) => {
  if (!id) return "";
  if (String(id).startsWith("ISS-")) return String(id);
  const n = parseInt(id, 10);
  return !isNaN(n) ? `ISS-${String(n).padStart(3, "0")}` : String(id);
};
const postDismiss = (payload) => {
  if (!payload) return;
  fetch(`${BACKEND}/jira/dismiss`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).catch(() => { });
};
const ssLoad  = () => { try { const r = sessionStorage.getItem(SS_KEY); return r ? JSON.parse(r) : null; } catch { return null; } };
const ssSave  = (v) => { try { sessionStorage.setItem(SS_KEY, JSON.stringify(v)); } catch {} };
const ssClear = () => { try { sessionStorage.removeItem(SS_KEY); } catch {} };

// ── Build the display title: "AppName (vX.Y.Z) — original title" ─────────────
const buildDisplayTitle = (payload) => {
  const base   = safeStr(pickFirst(payload, ["title", "issue_summary", "summary"]));
  const app    = safeStr(payload?.app_name    || "").trim();
  const ver    = safeStr(payload?.app_version || "").trim();
  const prefix = app
    ? ver ? `${app} (v${ver})` : app
    : "";
  return prefix ? `${prefix} — ${base}` : base;
};

const emptyIssue = () => ({
  source: "manual", jiraUrl: "", issueId: "", title: "", description: "",
  developer: "Unassigned", priority: "Medium", parent: "", fixVersion: "",
  affectsVersion: "", startDate: "", endDate: "", sprint: "",
  app_name: "", app_version: "", module: "", feature: "",
  test_name: "", steps_executed: [], issue_summary: "",
  ticket_id: "", internal_issue_id: "", created: false, rawPayload: null,
});

const mapPayloadToIssue = (payload) => ({
  ...emptyIssue(),
  source:            "draft",
  issueId:           safeStr(pickFirst(payload, ["jira_key", "jira_issue_key"])),
  jiraUrl:           safeStr(pickFirst(payload, ["jira_url", "issue_url", "browse_url", "url"])),
  // ── FIX 1: prefix title with app name + version ───────────────────────────
  title:             buildDisplayTitle(payload),
  description:       safeStr(payload.description || ""),
  developer:         safeStr(pickFirst(payload, ["developer_name", "developerName"])) || "Unassigned",
  parent:            safeStr(payload.parent || payload.module || ""),
  // ── FIX 2: map fix/affects version from payload ───────────────────────────
  fixVersion:        toArr(payload.fix_version    ?? payload.fixVersion).join(", "),
  affectsVersion:    toArr(payload.affects_version ?? payload.affectsVersion).join(", "),
  startDate:         safeStr(payload.start_date || "").slice(0, 10),
  endDate:           safeStr(payload.end_date   || "").slice(0, 10),
  sprint:            safeStr(payload.sprint     || "Automation"),
  priority:          safeStr(payload.priority   || "High"),
  app_name:          safeStr(payload.app_name),
  app_version:       safeStr(payload.app_version),
  module:            safeStr(payload.module || ""),
  feature:           safeStr(payload.feature),
  test_name:         safeStr(payload.test_name),
  steps_executed:    Array.isArray(payload.steps_executed) ? payload.steps_executed : [],
  issue_summary:     safeStr(payload.issue_summary) || safeStr(payload.title),
  ticket_id:         safeStr(payload.ticket_id),
  internal_issue_id: formatIssueId(safeStr(payload.issue_id)),
  created:           !!(safeStr(pickFirst(payload, ["jira_key", "jira_issue_key"])) && safeStr(pickFirst(payload, ["jira_url", "issue_url"]))),
  rawPayload:        payload,
});

/* ─── Styles ──────────────────────────────────────────────────────────────── */
const S = {
  label: {
    fontSize: "0.7rem", fontWeight: 600, color: "#64748B",
    marginBottom: "3px", display: "block", letterSpacing: "0.01em",
  },
  input: (locked) => ({
    width: "100%", boxSizing: "border-box",
    background: locked ? "#F8FAFC" : "#FFFFFF",
    border: "1px solid #E2E8F0",
    borderRadius: "6px",
    padding: "5px 8px", fontSize: "0.78rem",
    color: locked ? "#94A3B8" : "#0F172A",
    cursor: locked ? "not-allowed" : "text",
    fontFamily: "inherit",
    transition: "border-color 0.15s",
  }),
  btn: (color, bg = "none") => ({
    display: "inline-flex", alignItems: "center", gap: "5px",
    background: bg === "none" ? "transparent" : bg,
    border: `1.5px solid ${color}`,
    borderRadius: "6px", padding: "5px 13px",
    cursor: "pointer", fontSize: "0.75rem", color,
    fontWeight: 700, fontFamily: "inherit",
    textDecoration: "none", whiteSpace: "nowrap",
    transition: "opacity 0.15s",
  }),
  badge: (bg, color) => ({
    fontSize: "0.63rem", fontWeight: 800, flexShrink: 0,
    background: bg, color, borderRadius: "4px", padding: "2px 7px",
    letterSpacing: "0.01em",
  }),
};

/* ─── IssueCard ──────────────────────────────────────────────────────────── */
function IssueCard({ iss, idx, isOpen, onToggle, onRemove, onCreated, serverReady }) {
  const [creating, setCreating] = useState(false);
  const [fields, setFields] = useState(iss);
  const [errMsg, setErrMsg] = useState(null);
  const [enhancing, setEnhancing] = useState(false);

  useEffect(() => { setFields(iss); }, [iss]);

  const setF = (f, v) => setFields(p => ({ ...p, [f]: v }));
  const isCreated = !!iss.created || (!!iss.issueId && !!iss.jiraUrl);
  const locked = isCreated;
  const pColor = PRIORITY_COLOR[fields.priority] ?? "#64748b";
  const displayId = iss.internal_issue_id || `ISS-${String(idx + 1).padStart(3, "0")}`;

  const handleEnhance = async () => {
    setEnhancing(true); setErrMsg(null);
    try {
      const payload = fields.rawPayload || {};
      const body = {
        ticket_id: fields.ticket_id || payload.ticket_id || "",
        issue_id: fields.internal_issue_id || payload.issue_id || "",
        title: fields.title || "",
        test_name: fields.test_name || "",
        // test_id: payload.test_id || null,
        app_name: fields.app_name || "",
        app_version: fields.app_version || "",
        module: fields.module || fields.parent || "",
        feature: fields.feature || "",
        description: fields.description || "",
        steps_executed: Array.isArray(fields.steps_executed) ? fields.steps_executed : [],
        developer_name: fields.developer !== "Unassigned" ? fields.developer : "",
        start_date: fields.startDate || "",
        end_date: fields.endDate || "",
        sprint: fields.sprint || "",
        affects_version: fields.affectsVersion ? fields.affectsVersion.split(",").map(s => s.trim()).filter(Boolean) : [],
        fix_version: fields.fixVersion ? fields.fixVersion.split(",").map(s => s.trim()).filter(Boolean) : [],
      };
      const res = await fetch(`${BACKEND}/llm/enhance`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      let data = {}; try { data = await res.json(); } catch (_) { }
      if (!res.ok) { setErrMsg(data?.detail || `Enhance failed: HTTP ${res.status}`); return; }
      // Apply directly into fields — no confirmation step
      setFields(prev => ({
        ...prev,
        title: data.title || prev.title,
        description: data.description || prev.description,
      }));
    } catch (e) {
      setErrMsg(`Enhance network error: ${e?.message || e}`);
    } finally { setEnhancing(false); }
  };

  const handleCreate = async () => {
    if (!serverReady === false) { setErrMsg("Old server.py running — restart backend"); return; }
    setCreating(true); setErrMsg(null);
    try {
      const body = {
        app_name:        fields.app_name        || "",
        app_version:     fields.app_version     || "",
        module:          fields.module          || fields.parent || "",
        feature:         fields.feature         || "",
        issue_summary:   fields.issue_summary   || fields.title  || "",
        test_name:       fields.test_name       || "",
        steps_executed:  Array.isArray(fields.steps_executed) && fields.steps_executed.length ? fields.steps_executed : [],
        developer_name:  fields.developer !== "Unassigned" ? fields.developer : "",
        title:           fields.title           || "",
        description:     fields.description     || "",
        parent:          fields.parent          || "",
        fix_version:     fields.fixVersion     ? fields.fixVersion.split(",").map(s => s.trim()).filter(Boolean)     : [],
        affects_version: fields.affectsVersion ? fields.affectsVersion.split(",").map(s => s.trim()).filter(Boolean) : [],
        priority:        fields.priority        || "High",
        ticket_id:       fields.ticket_id       || "",
        start_date:      fields.startDate       || "",
        end_date:        fields.endDate         || "",
        sprint:          fields.sprint          || "Automation",
      };
      const res = await fetch(`${BACKEND}/jira/create`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      let data = {}; try { data = await res.json(); } catch (_) { }
      if (!res.ok) { setErrMsg(data?.detail || `HTTP ${res.status}`); return; }

      const issueKey = data.issue_id || data.issue_key || "";
      const jiraUrl = data.issue_url || (issueKey ? `https://malothram70.atlassian.net/browse/${issueKey}` : "");
      postDismiss(iss.rawPayload || { test_name: iss.test_name, module: iss.module, issue_summary: iss.issue_summary });
      onCreated({ ...iss, issueId: issueKey, jiraUrl, created: true });
    } catch (e) {
      setErrMsg(`Network error: ${e?.message || e}`);
    } finally { setCreating(false); }
  };

  return (
    <div style={{ borderLeft: `3px solid ${pColor}`, borderRadius: "6px", border: "1px solid #E2E8F0", marginBottom: "4px", background: "#FFFFFF", overflow: "hidden" }}>
      {/* Child row */}
      <button onClick={onToggle} style={{ width: "100%", display: "flex", alignItems: "center", gap: "6px", padding: "6px 10px", background: isOpen ? "#F8FAFC" : "transparent", border: "none", cursor: "pointer", textAlign: "left", borderBottom: isOpen ? "1px solid #E2E8F0" : "none", borderRadius: isOpen ? "4px 4px 0 0" : "4px" }}>
        {isOpen ? <ChevronDown size={12} color="var(--text-secondary)" /> : <ChevronRight size={12} color="var(--text-secondary)" />}
        <span style={S.badge("#dbeafe",  "#1d4ed8")}>AUTO</span>
        {fields.module && <span style={S.badge("#ede9fe",  "#7c3aed")}>{fields.module}</span>}
        <span style={{ color:  "var(--accent-blue)", fontWeight:  700, fontSize:  "0.76rem", flexShrink:  0 }}>
          {iss.issueId || displayId}
        </span>
        <span style={{ flex:  1, fontSize:  "0.76rem", color:  "var(--text-primary)", overflow:  "hidden", textOverflow:  "ellipsis", whiteSpace:  "nowrap" }}>
          {fields.title || <em style={{ color:  "var(--text-secondary)" }}>Untitled</em>}
        </span>
        {isCreated && <span style={S.badge("#dcfce7",  "#16a34a")}>✓ Created</span>}
        <span style={{ color:  pColor, fontSize:  "0.68rem", fontWeight:  700, flexShrink:  0 }}>{fields.priority}</span>
      </button>

      {/* Expanded body */}
      {isOpen && (
        <div style={{ padding:  "10px 12px", display:  "flex", flexDirection:  "column", gap:  "8px" }}>

          {/* Jira Key + Title */}
          <div style={{ display:  "flex", gap:  "7px" }}>
            <div style={{ flex:  "0 0 32%" }}>
              <label style={S.label}>Jira Issue Key</label>
              <input style={S.input(true)} value={iss.issueId} readOnly placeholder={displayId} />
            </div>
            <div style={{ flex:  1 }}>
              <label style={S.label}>Title <span style={{ color:  "#ef4444" }}>*</span></label>
              <input style={S.input(locked)} value={fields.title} readOnly={locked}
                onChange={e => !locked && setF("title", e.target.value)} />
            </div>
          </div>

          {/* Description */}
          <div>
            <label style={S.label}>Description <span style={{ color:  "#ef4444" }}>*</span></label>
            <textarea style={{ ...S.input(locked), resize:  "vertical", minHeight:  "260px", fontFamily:  "inherit", fontSize:  "0.71rem", lineHeight:  "1.5" }}
              value={fields.description} readOnly={locked}
              onChange={e => !locked && setF("description", e.target.value)} />
          </div>

          {/* Developer + Priority */}
          <div style={{ display:  "flex", gap:  "7px" }}>
            <div style={{ flex:  1 }}>
              <label style={S.label}>Developer</label>
              {locked ? <input style={S.input(true)} value={fields.developer} readOnly /> :
                <select style={S.input(false)} value={fields.developer} onChange={e => setF("developer", e.target.value)}>
                  {!DEVELOPERS.includes(fields.developer) && <option value={fields.developer}>{fields.developer}</option>}
                  {DEVELOPERS.map(d => <option key={d}>{d}</option>)}
                </select>}
            </div>
            <div style={{ flex:  1 }}>
              <label style={S.label}>Priority</label>
              {locked ? <input style={S.input(true)} value={fields.priority} readOnly /> :
                <select style={S.input(false)} value={fields.priority} onChange={e => setF("priority", e.target.value)}>
                  {PRIORITIES.map(p => <option key={p}>{p}</option>)}
                </select>}
            </div>
          </div>

          {/* Parent + Sprint */}
          <div style={{ display:  "flex", gap:  "7px" }}>
            <div style={{ flex:  1 }}>
              <label style={S.label}>Parent (Module)</label>
              <input style={S.input(locked)} value={fields.parent} readOnly={locked} onChange={e => !locked && setF("parent", e.target.value)} />
            </div>
            <div style={{ flex:  1 }}>
              <label style={S.label}>Sprint</label>
              <input style={S.input(locked)} value={fields.sprint} readOnly={locked} onChange={e => !locked && setF("sprint", e.target.value)} />
            </div>
          </div>

          {/* Fix + Affects Version */}
          <div style={{ display: "flex", gap: "7px" }}>
            <div style={{ flex: 1 }}>
              <label style={S.label}>Fix Version</label>
              <input style={S.input(locked)} value={fields.fixVersion} readOnly={locked}
                placeholder="e.g. Production"
                onChange={e => !locked && setF("fixVersion", e.target.value)} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={S.label}>Affects Version</label>
              <input style={S.input(locked)} value={fields.affectsVersion} readOnly={locked}
                placeholder="e.g. Krishivaas Farmer"
                onChange={e => !locked && setF("affectsVersion", e.target.value)} />
            </div>
          </div>

          {/* Dates */}
          <div style={{ display: "flex", gap: "7px" }}>
            <div style={{ flex: 1 }}>
              <label style={S.label}>Start Date</label>
              <input type="date" style={S.input(locked)} value={fields.startDate} readOnly={locked}
                onChange={e => !locked && setF("startDate", e.target.value)} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={S.label}>End Date (Due)</label>
              <input type="date" style={S.input(locked)} value={fields.endDate} readOnly={locked}
                onChange={e => !locked && setF("endDate", e.target.value)} />
            </div>
          </div>

          {/* Jira link */}
          {iss.jiraUrl && (
            <div style={{ fontSize: "0.71rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "5px" }}>
              <span>Jira:</span>
              <a href={iss.jiraUrl} target="_blank" rel="noreferrer" style={{ color: "var(--accent-blue)", fontWeight: 700, textDecoration: "none" }}>{iss.issueId} ↗</a>
            </div>
          )}

          {/* Error banner */}
          {errMsg && (
            <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "5px", padding: "8px 10px", fontSize: "0.71rem", color: "#b91c1c", lineHeight: "1.6" }}>
              <strong>⚠️ Create failed:</strong> {errMsg}
              <div style={{ marginTop: "4px" }}>
                <a href={`${BACKEND}/jira/test-connection`} target="_blank" rel="noreferrer" style={{ color: "#b91c1c", fontWeight: 700 }}>Test connection ↗</a>
              </div>
            </div>
          )}

          {/* Buttons */}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", paddingBottom: "2px" }}>
            {!isCreated && <button onClick={onRemove} style={S.btn("#ef4444")}>✕ Remove</button>}
            {isCreated && iss.jiraUrl && (
              <a href={iss.jiraUrl} target="_blank" rel="noreferrer" style={S.btn("#16a34a")}>
                <ExternalLink size={12} /> Open in Jira
              </a>
            )}
            {!isCreated && (
              <button
                onClick={handleEnhance}
                disabled={enhancing || creating}
                style={{
                  ...S.btn("#7c3aed"),
                  opacity: (enhancing || creating) ? 0.5 : 1,
                  cursor: (enhancing || creating) ? "not-allowed" : "pointer",
                }}
              >
                {enhancing ? "Enhancing…" : "✨ Enhance"}
              </button>
            )}
            {!isCreated && (
              <button onClick={handleCreate}
                disabled={!fields.title.trim() || !fields.description.trim() || creating}
                className="run-button"
                style={{
                  padding: "5px 20px", fontSize: "0.8rem", minWidth: "90px",
                  opacity: (!fields.title.trim() || !fields.description.trim()) ? 0.4 : 1,
                  cursor: (!fields.title.trim() || !fields.description.trim() || creating) ? "not-allowed" : "pointer",
                }}>
                {creating ? "Creating…" : "Create"}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── RunGroup ───────────────────────────────────────────────────────────── */
function RunGroup({ ticketId, issues, openChildren, onToggleChild, onRemoveIssue, onIssueCreated, serverReady, isGroupOpen, onToggleGroup }) {
  const total   = issues.length;
  const created = issues.filter(i => i.created || (i.issueId && i.jiraUrl)).length;
  const pending = total - created;

  return (
    <div style={{ border: "1px solid #E2E8F0", borderRadius: "8px", background: "#FFFFFF", marginBottom: "6px", overflow: "hidden" }}>
      <button onClick={onToggleGroup} style={{ width: "100%", display: "flex", alignItems: "center", gap: "8px", padding: "9px 12px", background: isGroupOpen ? "#F8FAFC" : "#FAFAFA", border: "none", cursor: "pointer", textAlign: "left", borderBottom: isGroupOpen ? "1px solid #E2E8F0" : "none" }}>
        {isGroupOpen ? <FolderOpen size={15} color="var(--accent-blue)" /> : <Folder size={15} color="var(--accent-blue)" />}
        {isGroupOpen ? <ChevronDown size={13} color="var(--text-secondary)" /> : <ChevronRight size={13} color="var(--text-secondary)" />}
        <span style={{ fontWeight: 800, fontSize: "0.8rem", color: "var(--accent-blue)", fontFamily: "monospace", letterSpacing: "0.03em" }}>
          {ticketId || "Manual Issues"}
        </span>
        <span style={{ fontSize: "0.68rem", color: "var(--text-secondary)", marginLeft: "4px" }}>Run ID</span>
        <div style={{ flex: 1 }} />
        {pending > 0 && <span style={S.badge("#fee2e2", "#dc2626")}>{pending} pending</span>}
        {created > 0 && <span style={S.badge("#dcfce7", "#16a34a")}>{created} created</span>}
        <span style={{ ...S.badge("var(--border-color)", "var(--text-secondary)") }}>{total} issue{total !== 1 ? "s" : ""}</span>
      </button>

      {isGroupOpen && (
        <div style={{ padding: "8px 10px" }}>
          {issues.map((iss, localIdx) => {
            const childKey = `${ticketId}::${iss.internal_issue_id || localIdx}`;
            return (
              <IssueCard
                key={childKey}
                iss={iss}
                idx={localIdx}
                isOpen={openChildren.has(childKey)}
                onToggle={() => onToggleChild(childKey)}
                onRemove={() => onRemoveIssue(ticketId, iss)}
                onCreated={(updated) => onIssueCreated(ticketId, iss, updated)}
                serverReady={serverReady}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── IssuePanel ─────────────────────────────────────────────────────────── */
export default function IssuePanel({ modules = [], jiraIssues = [], onHistoryUpdate = null }) {
  const [issues,       setIssues]      = useState(() => ssLoad() || []);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [wsConnected,  setWsConnected]  = useState(false);
  const [serverReady,  setServerReady]  = useState(null);
  const [openGroups,   setOpenGroups]   = useState(() => new Set());
  const [openChildren, setOpenChildren] = useState(() => new Set());

  const importedKeys = useRef(new Set(
    (ssLoad() || []).map(iss => dedupKey(iss.rawPayload || iss))
  ));

  useEffect(() => { ssSave(issues); }, [issues]);

  // useEffect(() => {
  //   fetch(`${BACKEND}jira/health`).then(r => r.json()).then(d => setServerReady(d.status === "ok")).catch(() => setServerReady(false));
  // }, []);

  const addPayload = useCallback((payload) => {
    if (!payload || typeof payload !== "object") return;
    const key = dedupKey(payload);
    if (importedKeys.current.has(key)) return;
    importedKeys.current.add(key);
    const issue = mapPayloadToIssue(payload);
    setIssues(prev => [...prev, issue]);
    const tid = safeStr(payload.ticket_id) || "manual";
    setOpenGroups(prev => new Set([...prev, tid]));
    const iid = formatIssueId(safeStr(payload.issue_id)) || String(Date.now());
    setOpenChildren(prev => new Set([...prev, `${tid}::${iid}`]));
    console.log(payload, issue);
  }, []);

  useEffect(() => {
    const saved = ssLoad();
    if (saved && saved.length > 0) return;
    fetch(`${BACKEND}/jira/payloads`).then(r => r.json()).then(d => {
      (d.payloads || []).forEach(addPayload);
    }).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let ws, dead = false;
    const connect = () => {
      try {
        ws = new WebSocket(WS_BACKEND);
        ws.onopen = () => setWsConnected(true);
        ws.onclose = () => { setWsConnected(false); if (!dead) setTimeout(connect, 3000); };
        ws.onerror = () => setWsConnected(false);
        ws.onmessage = (evt) => {
          try {
            const msg = JSON.parse(evt.data);
            if (msg.type === "RUN_START") {
              importedKeys.current = new Set();
              setIssues([]); ssClear();
              setOpenGroups(new Set()); setOpenChildren(new Set());
              return;
            }
            if (msg.type === "JIRA_PAYLOAD" && msg.payload) { addPayload(msg.payload); return; }
            if (msg.type === "LOG" && msg.payload?.message) {
              const p = parsePayloadFromLogLine(msg.payload.message);
              if (p) addPayload(p);
            }
          } catch (_) { }
        };
      } catch (_) { if (!dead) setTimeout(connect, 3000); }
    };
    connect();
    return () => { dead = true; try { ws?.close(); } catch (_) { } };
  }, [addPayload]);

  useEffect(() => {
    (Array.isArray(jiraIssues) ? jiraIssues : []).forEach(addPayload);
  }, [jiraIssues, addPayload]);

  const groupedMap = {};
  issues.forEach(iss => {
    const tid = iss.ticket_id || "manual";
    if (!groupedMap[tid]) groupedMap[tid] = [];
    groupedMap[tid].push(iss);
  });
  const sortedTicketIds = Object.keys(groupedMap).sort((a, b) => b.localeCompare(a));

  const totalIssues = issues.length;
  const totalCreated = issues.filter(i => i.created || (i.issueId && i.jiraUrl)).length;

  const toggleGroup = (tid) => setOpenGroups(prev => {
    const next = new Set(prev);
    next.has(tid) ? next.delete(tid) : next.add(tid);
    return next;
  });
  const toggleChild = (key) => setOpenChildren(prev => {
    const next = new Set(prev);
    next.has(key) ? next.delete(key) : next.add(key);
    return next;
  });

  const removeIssue = (ticketId, iss) => {
    postDismiss(iss.rawPayload || { test_name: iss.test_name, module: iss.module, issue_summary: iss.issue_summary });
    setIssues(prev => prev.filter(i => dedupKey(i) !== dedupKey(iss)));
    if (typeof onHistoryUpdate === "function") {
      onHistoryUpdate({
        type: "removed", savedAt: new Date().toISOString(),
        ticketId,
        title: iss.title || iss.issue_summary || "Untitled",
        module: iss.module || iss.parent || "",
        priority: iss.priority || "Medium",
        developer: iss.developer || "Unassigned",
        app_name: iss.app_name || "",
        app_version: iss.app_version || "",
        test_name: iss.test_name || "",
        issueId: "",
        internal_issue_id: iss.internal_issue_id || "",
        jiraUrl:           "",
        steps_executed:    Array.isArray(iss.steps_executed) ? iss.steps_executed : [],
        description:       iss.description       || "",
        sprint:            iss.sprint            || "",
        fix_version:       iss.fixVersion     ? iss.fixVersion.split(",").map(s => s.trim()).filter(Boolean)     : [],
        affects_version:   iss.affectsVersion ? iss.affectsVersion.split(",").map(s => s.trim()).filter(Boolean) : [],
        start_date:        iss.startDate         || "",
        end_date:          iss.endDate           || "",
      });
    }
  };

  const issueCreated = (ticketId, oldIss, updatedIss) => {
    setIssues(prev => prev.filter(i => dedupKey(i) !== dedupKey(oldIss)));
    if (typeof onHistoryUpdate === "function") {
      onHistoryUpdate({
        type: "created", savedAt: new Date().toISOString(),
        ticketId,
        issueId: updatedIss.issueId,
        jiraUrl: updatedIss.jiraUrl,
        title: updatedIss.title || "Untitled",
        module: updatedIss.module || "",
        priority: updatedIss.priority || "High",
        developer: updatedIss.developer || "",
        app_name: updatedIss.app_name || "",
        app_version: updatedIss.app_version || "",
        test_name: updatedIss.test_name || "",
        internal_issue_id: updatedIss.internal_issue_id || "",
        steps_executed:    Array.isArray(updatedIss.steps_executed) ? updatedIss.steps_executed : [],
        description:       updatedIss.description       || "",
        sprint:            updatedIss.sprint            || "",
        // ── FIX: pass both version arrays to JiraHistory ──────────────────
        fix_version:       updatedIss.fixVersion
          ? updatedIss.fixVersion.split(",").map(s => s.trim()).filter(Boolean)
          : [],
        affects_version:   updatedIss.affectsVersion
          ? updatedIss.affectsVersion.split(",").map(s => s.trim()).filter(Boolean)
          : [],
        start_date:        updatedIss.startDate         || "",
        end_date:          updatedIss.endDate           || "",
        created_at:        new Date().toISOString(),
      });
    }
  };

  /* ─── Render ──────────────────────────────────────────────────────────── */
  return (
    <div style={{
      display: "flex", flexDirection: "column",
      /* On large screens the wrapper div is stretched by the flex parent,
         so height: 100% fills the full panel height without overflow.
         Full-screen mode overrides to 100vh. */
      height: isFullScreen ? "100vh" : "100%",
      minHeight: "360px",
      ...(isFullScreen
        ? { position: "fixed", inset: 0, zIndex: 9999, borderRadius: 0 }
        : { borderRadius: "14px" }),
      background: "#FFFFFF",
      border: "1px solid #E2E8F0",
      overflow: "hidden",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif",
      boxShadow: "0 1px 3px rgba(15,23,42,.06), 0 1px 2px rgba(15,23,42,.04)",
    }}>

      {serverReady === false && (
        <div style={{ background: "#FEF2F2", borderBottom: "1px solid #FECACA", padding: "5px 12px", fontSize: "0.7rem", color: "#B91C1C", flexShrink: 0 }}>
          ⚠️ Old server detected — restart backend with new server.py
        </div>
      )}

      {/* ── Header ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.6rem 0.85rem", borderBottom: "1px solid #E2E8F0", background: "#F8FAFC", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
          <AlertCircle size={13} color="#2563EB" />
          <span style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".06em", color: "#64748B" }}>Issue List</span>
          <span title={wsConnected ? "Connected" : "Disconnected"}>
            {wsConnected ? <Wifi size={11} color="#059669" /> : <WifiOff size={11} color="#DC2626" />}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          {[`${totalIssues} issues`, `${sortedTicketIds.length} run${sortedTicketIds.length !== 1 ? "s" : ""}`, `${totalCreated} created`].map(lbl => (
            <span key={lbl} style={{ fontSize: "0.63rem", color: "#64748B", background: "#F1F5F9", border: "1px solid #E2E8F0", borderRadius: "999px", padding: "2px 8px", fontWeight: 600 }}>{lbl}</span>
          ))}
          <button onClick={() => setIsFullScreen(f => !f)} style={{ background: "none", border: "none", cursor: "pointer", color: "#94A3B8", display: "flex", alignItems: "center", padding: "3px", marginLeft: "2px" }}>
            {isFullScreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </button>
        </div>
      </div>

      {/* ── Groups list ── */}
      <div style={{ flex: 1, overflowY: "auto", overflowX: "hidden", padding: "8px", display: "flex", flexDirection: "column", minHeight: 0, scrollbarWidth: "thin", scrollbarColor: "#E2E8F0 transparent" }}>
        {sortedTicketIds.length === 0 && (
          <div style={{ textAlign: "center", color: "#94A3B8", fontSize: "0.78rem", padding: "32px 16px", lineHeight: "1.6" }}>
            <div style={{ fontSize: "1.6rem", marginBottom: "8px" }}>🔍</div>
            {wsConnected
              ? "Waiting for test failures…\nFailed test issues appear here automatically."
              : "WebSocket disconnected — is backend running?"}
          </div>
        )}
        {sortedTicketIds.map(tid => (
          <RunGroup
            key={tid}
            ticketId={tid === "manual" ? "" : tid}
            issues={groupedMap[tid]}
            openChildren={openChildren}
            onToggleChild={toggleChild}
            onRemoveIssue={removeIssue}
            onIssueCreated={issueCreated}
            serverReady={serverReady}
            isGroupOpen={openGroups.has(tid)}
            onToggleGroup={() => toggleGroup(tid)}
          />
        ))}
      </div>
    </div>
  );
}