import { useState } from "react";
import axios from "axios";
import { useApiStore } from "../../store/useApiStore";
import SidebarPanel from "./SidebarPanel";
import "./ApiTesterPro.css";

export default function AdvancedApiTester() {
  const {
    activeRequest,
    setActiveRequest,
    loadRequest,
    addCollection,
    addHistory,
    resolveUrl,
  } = useApiStore();

  const { method, url, headers, params, body } = activeRequest;

  const [response, setResponse] = useState(null);
  const [status, setStatus] = useState(null);
  const [time, setTime] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("params");

  const updateRow = (key, list, index, field, value) => {
    const updated = [...list];
    updated[index][field] = value;
    setActiveRequest({ [key]: updated });
  };

  const addRow = (key, list) => {
    setActiveRequest({ [key]: [...list, { key: "", value: "" }] });
  };

  const sendRequest = async () => {
    try {
      setLoading(true);

      const headersObj = Object.fromEntries(
        headers.filter(h => h.key).map(h => [h.key, h.value])
      );

      const paramsObj = Object.fromEntries(
        params.filter(p => p.key).map(p => [p.key, p.value])
      );

      const finalUrl = resolveUrl(url);

      const start = Date.now();

      const res = await axios({
        method,
        url: finalUrl,
        headers: headersObj,
        params: paramsObj,
        data: body ? JSON.parse(body) : undefined,
      });

      const end = Date.now();

      setResponse(res.data);
      setStatus(res.status);
      setTime(end - start);

      addHistory({ method, url });

    } catch (err) {
      setResponse({ error: err.message });
      setStatus("ERROR");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="full-layout">

      {/* SIDEBAR */}
      <SidebarPanel loadRequest={loadRequest} />

      {/* MAIN */}
      <div className="api-root">

        {/* TOP BAR */}
        <div className="topbar">
          <select value={method} onChange={(e) => setActiveRequest({ method: e.target.value })}>
            {["GET", "POST", "PUT", "PATCH", "DELETE"].map(m => (
              <option key={m}>{m}</option>
            ))}
          </select>

          <input
            value={url}
            onChange={(e) => setActiveRequest({ url: e.target.value })}
            placeholder="https://api.example.com"
          />

          <button onClick={sendRequest}>
            {loading ? "Sending..." : "Send"}
          </button>

          <button onClick={() => addCollection(activeRequest)}>
            Save
          </button>
        </div>

        {/* TABS */}
        <div className="tabs">
          {["params", "headers", "body"].map(t => (
            <button
              key={t}
              className={tab === t ? "active" : ""}
              onClick={() => setTab(t)}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>

        {/* PARAMS */}
        <div className="tab-content">
          {tab === "params" &&
            params.map((p, i) => (
              <div key={i} className="row">
                <input
                  value={p.key}
                  placeholder="Key"
                  onChange={(e) => updateRow("params", params, i, "key", e.target.value)}
                />
                <input
                  value={p.value}
                  placeholder="Value"
                  onChange={(e) => updateRow("params", params, i, "value", e.target.value)}
                />
              </div>
            ))}

          {tab === "headers" &&
            headers.map((h, i) => (
              <div key={i} className="row">
                <input
                  value={h.key}
                  placeholder="Key"
                  onChange={(e) => updateRow("headers", headers, i, "key", e.target.value)}
                />
                <input
                  value={h.value}
                  placeholder="Value"
                  onChange={(e) => updateRow("headers", headers, i, "value", e.target.value)}
                />
              </div>
            ))}

          {tab === "body" && (
            <textarea
              value={body}
              onChange={(e) => setActiveRequest({ body: e.target.value })}
            />
          )}

          <button className="add-btn" onClick={() => addRow(tab, activeRequest[tab])}>
            + Add
          </button>
        </div>

        {/* META */}
        <div className="response-meta">
          {status && <span>Status: {status}</span>}
          {time && <span>Time: {time} ms</span>}
        </div>

        {/* RESPONSE */}
        <div className="response">
          {response ? (
            <pre>{JSON.stringify(response, null, 2)}</pre>
          ) : (
            "No response yet"
          )}
        </div>

      </div>
    </div>
  );
}