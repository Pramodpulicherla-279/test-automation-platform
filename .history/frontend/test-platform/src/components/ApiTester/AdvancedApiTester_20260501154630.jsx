import { useState } from "react";
import axios from "axios";
import "./ApiTester.css";

export default function AdvancedApiTester() {
  const [method, setMethod] = useState("GET");
  const [url, setUrl] = useState("");
  const [headers, setHeaders] = useState([{ key: "", value: "" }]);
  const [params, setParams] = useState([{ key: "", value: "" }]);
  const [body, setBody] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("params");

  const sendRequest = async () => {
    try {
      setLoading(true);

      const headersObj = Object.fromEntries(
        headers.filter(h => h.key).map(h => [h.key, h.value])
      );

      const paramsObj = Object.fromEntries(
        params.filter(p => p.key).map(p => [p.key, p.value])
      );

      const res = await axios({
        method,
        url,
        headers: headersObj,
        params: paramsObj,
        data: body ? JSON.parse(body) : undefined,
      });

      setResponse(res.data);
    } catch (err) {
      setResponse({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const update = (setter, list, i, field, value) => {
    const updated = [...list];
    updated[i][field] = value;
    setter(updated);
  };

  return (
    <div className="api-container">
      {/* TOP BAR */}
      <div className="topbar">
        <select value={method} onChange={e => setMethod(e.target.value)}>
          {["GET", "POST", "PUT", "PATCH", "DELETE"].map(m => (
            <option key={m}>{m}</option>
          ))}
        </select>

        <input
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="Enter API URL..."
        />

        <button onClick={sendRequest}>
          {loading ? "Sending..." : "Send"}
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

      {/* TAB CONTENT */}
      <div className="tab-content">
        {tab === "params" &&
          params.map((p, i) => (
            <div key={i} className="row">
              <input
                placeholder="Key"
                value={p.key}
                onChange={e =>
                  update(setParams, params, i, "key", e.target.value)
                }
              />
              <input
                placeholder="Value"
                value={p.value}
                onChange={e =>
                  update(setParams, params, i, "value", e.target.value)
                }
              />
            </div>
          ))}

        {tab === "headers" &&
          headers.map((h, i) => (
            <div key={i} className="row">
              <input
                placeholder="Key"
                value={h.key}
                onChange={e =>
                  update(setHeaders, headers, i, "key", e.target.value)
                }
              />
              <input
                placeholder="Value"
                value={h.value}
                onChange={e =>
                  update(setHeaders, headers, i, "value", e.target.value)
                }
              />
            </div>
          ))}

        {tab === "body" && (
          <textarea
            placeholder="JSON body..."
            value={body}
            onChange={e => setBody(e.target.value)}
          />
        )}
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
  );
}