import { useState } from "react";
import axios from "axios";
import "./ApiTesterPro.css";

export default function AdvancedApiTester() {
  const [method, setMethod] = useState("GET");
  const [url, setUrl] = useState("");
  const [params, setParams] = useState([{ key: "", value: "" }]);
  const [headers, setHeaders] = useState([{ key: "", value: "" }]);
  const [body, setBody] = useState("");
  const [response, setResponse] = useState(null);
  const [status, setStatus] = useState(null);
  const [time, setTime] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("params");

  const updateRow = (setter, list, index, field, value) => {
    const updated = [...list];
    updated[index][field] = value;
    setter(updated);
  };

  const addRow = (setter, list) => {
    setter([...list, { key: "", value: "" }]);
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

      const start = Date.now();

      const res = await axios({
        method,
        url,
        headers: headersObj,
        params: paramsObj,
        data: body ? JSON.parse(body) : undefined,
      });

      const end = Date.now();

      setResponse(res.data);
      setStatus(res.status);
      setTime(end - start);
    } catch (err) {
      setResponse({ error: err.message });
      setStatus("ERROR");
      setTime(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="api-root">

      {/* TOP BAR */}
      <div className="topbar">
        <select value={method} onChange={(e) => setMethod(e.target.value)}>
          {["GET", "POST", "PUT", "PATCH", "DELETE"].map((m) => (
            <option key={m}>{m}</option>
          ))}
        </select>

        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://api.example.com"
        />

        <button onClick={sendRequest}>
          {loading ? "Sending..." : "Send"}
        </button>
      </div>

      {/* TABS */}
      <div className="tabs">
        {["params", "headers", "body"].map((t) => (
          <button
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => setTab(t)}
          >
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      {/* TAB CONTENT */}
      <div className="tab-content">

        {tab === "params" && (
          <>
            {params.map((p, i) => (
              <div key={i} className="row">
                <input
                  placeholder="Key"
                  value={p.key}
                  onChange={(e) =>
                    updateRow(setParams, params, i, "key", e.target.value)
                  }
                />
                <input
                  placeholder="Value"
                  value={p.value}
                  onChange={(e) =>
                    updateRow(setParams, params, i, "value", e.target.value)
                  }
                />
              </div>
            ))}
            <button className="add-btn" onClick={() => addRow(setParams, params)}>
              + Add Param
            </button>
          </>
        )}

        {tab === "headers" && (
          <>
            {headers.map((h, i) => (
              <div key={i} className="row">
                <input
                  placeholder="Key"
                  value={h.key}
                  onChange={(e) =>
                    updateRow(setHeaders, headers, i, "key", e.target.value)
                  }
                />
                <input
                  placeholder="Value"
                  value={h.value}
                  onChange={(e) =>
                    updateRow(setHeaders, headers, i, "value", e.target.value)
                  }
                />
              </div>
            ))}
            <button className="add-btn" onClick={() => addRow(setHeaders, headers)}>
              + Add Header
            </button>
          </>
        )}

        {tab === "body" && (
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder='{"key":"value"}'
          />
        )}
      </div>

      {/* RESPONSE HEADER */}
      <div className="response-meta">
        {status && <span>Status: {status}</span>}
        {time && <span>Time: {time} ms</span>}
      </div>

      {/* RESPONSE BODY */}
      <div className="response">
        {response ? (
          <pre>{JSON.stringify(response, null, 2)}</pre>
        ) : (
          "No response yet"
        )}
      </div>
    </div>
  );
}