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
  } = useApiStore();

  const { method, url, headers, params, body } = activeRequest;

  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("params");

  const updateRow = (key, list, i, field, value) => {
    const updated = [...list];
    updated[i][field] = value;
    setActiveRequest({ [key]: updated });
  };

  const addRow = (key, list) => {
    setActiveRequest({
      [key]: [...list, { key: "", value: "" }],
    });
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

      const res = await axios({
        method,
        url,
        headers: headersObj,
        params: paramsObj,
        data: body ? JSON.parse(body) : undefined,
      });

      setResponse(res.data);
      addHistory({ method, url });

    } catch (err) {
      setResponse({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="full-layout">

      <SidebarPanel loadRequest={loadRequest} />

      <div className="api-root">

        {/* TOP */}
        <div className="topbar">
          <select
            value={method}
            onChange={(e) =>
              setActiveRequest({ method: e.target.value })
            }
          >
            {["GET", "POST", "PUT", "PATCH", "DELETE"].map(m => (
              <option key={m}>{m}</option>
            ))}
          </select>

          <input
            value={url}
            onChange={(e) =>
              setActiveRequest({ url: e.target.value })
            }
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

        {/* CONTENT */}
        <div className="tab-content">

          {(tab === "params" || tab === "headers") &&
            activeRequest[tab].map((row, i) => (
              <div key={i} className="row">
                <input
                  placeholder="Key"
                  value={row.key}
                  onChange={(e) =>
                    updateRow(tab, activeRequest[tab], i, "key", e.target.value)
                  }
                />
                <input
                  placeholder="Value"
                  value={row.value}
                  onChange={(e) =>
                    updateRow(tab, activeRequest[tab], i, "value", e.target.value)
                  }
                />
              </div>
            ))}

          {tab === "body" && (
            <textarea
              value={body}
              onChange={(e) =>
                setActiveRequest({ body: e.target.value })
              }
            />
          )}

          <button
            className="add-btn"
            onClick={() => addRow(tab, activeRequest[tab])}
          >
            + Add
          </button>

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