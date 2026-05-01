import { useState } from "react";
import axios from "axios";
import { useApiStore } from "../../store/useApiStore";
import SidebarPanel from "./SidebarPanel";
import "./ApiTesterPro.css";

export default function AdvancedApiTester() {
  const {
    tabs,
    activeTabId,
    addTab,
    setActiveTab,
    updateRequest,
    setResponse,
  } = useApiStore();

  const tab = tabs.find((t) => t.id === activeTabId);
  const req = tab?.request || {};

  const [activeSection, setActiveSection] = useState("params");

  const sendRequest = async () => {
    const start = Date.now();

    try {
      const headersObj = Object.fromEntries(
        (req.headers || []).filter(h => h.key).map(h => [h.key, h.value])
      );

      // 🔐 AUTH SUPPORT
      if (req.auth?.type === "bearer") {
        headersObj["Authorization"] = `Bearer ${req.auth.token}`;
      }

      const res = await axios({
        method: req.method,
        url: req.url,
        headers: headersObj,
        params: Object.fromEntries(
          (req.params || []).filter(p => p.key).map(p => [p.key, p.value])
        ),
        data: req.body ? JSON.parse(req.body || "{}") : undefined,
      });

      const end = Date.now();

      setResponse(res.data, res.status, end - start);

    } catch (err) {
      setResponse(
        { error: err.message },
        err.response?.status || 500,
        0
      );
    }
  };

  const updateRow = (type, index, field, value) => {
    const updated = [...(req[type] || [])];
    updated[index][field] = value;
    updateRequest({ [type]: updated });
  };

  const addRow = (type) => {
    updateRequest({
      [type]: [...(req[type] || []), { key: "", value: "" }],
    });
  };

  return (
    <div className="full-layout">

      {/* ===== SIDEBAR (UNCHANGED) ===== */}
      <SidebarPanel />

      {/* ===== MAIN ===== */}
      <div className="api-root">

        {/* ===== TABS (NEW) ===== */}
        <div className="tab-bar">
          {tabs.map((t) => (
            <div
              key={t.id}
              className={`tab ${t.id === activeTabId ? "active" : ""}`}
              onClick={() => setActiveTab(t.id)}
            >
              {t.name}
            </div>
          ))}
          <button onClick={addTab}>+</button>
        </div>

        {/* ===== TOP BAR ===== */}
        <div className="topbar">

          <select
            value={req.method}
            onChange={(e) =>
              updateRequest({ method: e.target.value })
            }
          >
            {["GET", "POST", "PUT", "DELETE"].map(m => (
              <option key={m}>{m}</option>
            ))}
          </select>

          <input
            value={req.url || ""}
            onChange={(e) =>
              updateRequest({ url: e.target.value })
            }
            placeholder="Enter URL"
          />

          <button onClick={sendRequest}>Send</button>
        </div>

        {/* ===== AUTH PANEL (NEW) ===== */}
        <div className="auth">
          <select
            value={req.auth?.type || "none"}
            onChange={(e) =>
              updateRequest({
                auth: { ...req.auth, type: e.target.value },
              })
            }
          >
            <option value="none">No Auth</option>
            <option value="bearer">Bearer Token</option>
          </select>

          {req.auth?.type === "bearer" && (
            <input
              placeholder="Enter token"
              value={req.auth.token || ""}
              onChange={(e) =>
                updateRequest({
                  auth: { ...req.auth, token: e.target.value },
                })
              }
            />
          )}
        </div>

        {/* ===== EXISTING TABS (RESTORED) ===== */}
        <div className="tabs">
          {["params", "headers", "body"].map((t) => (
            <button
              key={t}
              className={activeSection === t ? "active" : ""}
              onClick={() => setActiveSection(t)}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>

        <div className="tab-content">

          {(activeSection === "params" || activeSection === "headers") &&
            (req[activeSection] || []).map((row, i) => (
              <div key={i} className="row">
                <input
                  placeholder="Key"
                  value={row.key}
                  onChange={(e) =>
                    updateRow(activeSection, i, "key", e.target.value)
                  }
                />
                <input
                  placeholder="Value"
                  value={row.value}
                  onChange={(e) =>
                    updateRow(activeSection, i, "value", e.target.value)
                  }
                />
              </div>
            ))}

          {activeSection === "body" && (
            <textarea
              value={req.body || ""}
              onChange={(e) =>
                updateRequest({ body: e.target.value })
              }
            />
          )}

          <button className="add-btn" onClick={() => addRow(activeSection)}>
            + Add
          </button>

        </div>

        {/* ===== RESPONSE (UPGRADED) ===== */}
        <div className="response">

          <div className="response-meta">
            Status: {tab?.status || "-"} |
            Time: {tab?.time ? `${tab.time} ms` : "-"}
          </div>

          <pre>
            {tab?.response
              ? JSON.stringify(tab.response, null, 2)
              : "No response yet"}
          </pre>

        </div>

      </div>
    </div>
  );
}