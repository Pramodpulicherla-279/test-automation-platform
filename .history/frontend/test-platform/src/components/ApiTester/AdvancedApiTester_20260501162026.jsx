import { useApiStore } from "../../store/useApiStore";
import axios from "axios";
import "./ApiTesterPro.css";

export default function AdvancedApiTester() {
  const {
    tabs,
    activeTabId,
    setActiveTab,
    addTab,
    updateRequest,
    setResponse,
  } = useApiStore();

  const tab = tabs.find((t) => t.id === activeTabId);
  const req = tab.request;

  const sendRequest = async () => {
    const start = Date.now();

    try {
      const headersObj = Object.fromEntries(
        (req.headers || []).filter(h => h.key).map(h => [h.key, h.value])
      );

      // AUTH SUPPORT
      if (req.auth.type === "bearer") {
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

  return (
    <div className="api-root">

      {/* ===== TABS ===== */}
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

      {/* ===== TOP ===== */}
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
          value={req.url}
          onChange={(e) =>
            updateRequest({ url: e.target.value })
          }
          placeholder="Enter URL"
        />

        <button onClick={sendRequest}>Send</button>
      </div>

      {/* ===== AUTH PANEL ===== */}
      <div className="auth">
        <select
          value={req.auth.type}
          onChange={(e) =>
            updateRequest({
              auth: { ...req.auth, type: e.target.value },
            })
          }
        >
          <option value="none">No Auth</option>
          <option value="bearer">Bearer Token</option>
        </select>

        {req.auth.type === "bearer" && (
          <input
            placeholder="Enter token"
            value={req.auth.token}
            onChange={(e) =>
              updateRequest({
                auth: { ...req.auth, token: e.target.value },
              })
            }
          />
        )}
      </div>

      {/* ===== RESPONSE ===== */}
      <div className="response">

        <div className="response-meta">
          Status: {tab.status || "-"} |
          Time: {tab.time ? `${tab.time} ms` : "-"}
        </div>

        <pre>
          {tab.response
            ? JSON.stringify(tab.response, null, 2)
            : "No response"}
        </pre>

      </div>
    </div>
  );
}