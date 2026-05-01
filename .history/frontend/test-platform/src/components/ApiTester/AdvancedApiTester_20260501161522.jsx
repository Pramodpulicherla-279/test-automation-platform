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
  const [speed, setSpeed] = useState("fast");

  // 🌐 Network throttling map
  const delayMap = {
    "2g": 2000,
    "3g": 1000,
    "4g": 300,
    "5g": 50,
    "fast": 0,
  };

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

  const sendRequest = async (customReq = null) => {
    const req = customReq || activeRequest;

    try {
      setLoading(true);

      // 🐢 simulate network speed
      await new Promise((res) =>
        setTimeout(res, delayMap[speed])
      );

      const headersObj = Object.fromEntries(
        (req.headers || []).filter(h => h.key).map(h => [h.key, h.value])
      );

      const paramsObj = Object.fromEntries(
        (req.params || []).filter(p => p.key).map(p => [p.key, p.value])
      );

      const res = await axios({
        method: req.method,
        url: req.url,
        headers: headersObj,
        params: paramsObj,
        data: req.body ? JSON.parse(req.body) : undefined,
      });

      setResponse(res.data);
      addHistory({ method: req.method, url: req.url });

    } catch (err) {
      setResponse({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="full-layout">

      {/* SIDEBAR */}
      <SidebarPanel
        loadRequest={loadRequest}
        runRequest={sendRequest}
      />

      {/* MAIN */}
      <div className="api-root">

        {/* TOP BAR */}
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

          {/* NETWORK THROTTLING */}
          <select
            value={speed}
            onChange={(e) => setSpeed(e.target.value)}
          >
            <option value="fast">No Limit</option>
            <option value="2g">2G</option>
            <option value="3g">3G</option>
            <option value="4g">4G</option>
            <option value="5g">5G</option>
          </select>

          <button onClick={() => sendRequest()}>
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
              placeholder='{"key":"value"}'
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