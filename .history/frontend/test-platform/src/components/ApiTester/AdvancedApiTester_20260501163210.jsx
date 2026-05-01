import { useState } from "react";
import { useApiStore } from "../../store/useApiStore";
import { sendRequest } from "../../utils/requestExecutor";
import "./ApiTesterPro.css";

export default function AdvancedApiTester() {
  const {
    collections,
    addCollection,
    saveRequest,
    deleteRequest,
    auth,
    setAuth,
    throttle,
    setThrottle
  } = useApiStore();

  const [tabs, setTabs] = useState([{ id: 1 }]);
  const [active, setActive] = useState(0);

  const [url, setUrl] = useState("");
  const [method, setMethod] = useState("GET");
  const [headers, setHeaders] = useState({});
  const [body, setBody] = useState("");
  const [tests, setTests] = useState("");

  const [response, setResponse] = useState(null);

  const handleSend = async () => {
    const res = await sendRequest({
      url,
      method,
      headers,
      body,
      auth,
      throttle,
      tests
    });
    setResponse(res);
  };

  return (
    <div className="full-layout">

      {/* SIDEBAR */}
      <div className="sidebar-panel">
        <button onClick={() => addCollection("New Collection")}>
          + Collection
        </button>

        {collections.map((col, ci) => (
          <div key={ci}>
            <b>{col.name}</b>

            {(col.requests || []).map((r, ri) => (
              <div key={ri} className="collection-item">
                {r.method}
                <button onClick={() => handleSend(r)}>▶</button>
                <button onClick={() => deleteRequest(ci, ri)}>🗑</button>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* MAIN */}
      <div className="api-root">

        {/* TABS */}
        <div className="tab-bar">
          {tabs.map((t, i) => (
            <div
              key={i}
              className={i === active ? "tab active" : "tab"}
              onClick={() => setActive(i)}
            >
              Tab {i + 1}
            </div>
          ))}
          <button onClick={() => setTabs([...tabs, { id: Date.now() }])}>
            +
          </button>
        </div>

        {/* TOP BAR */}
        <div className="topbar">
          <select value={method} onChange={(e) => setMethod(e.target.value)}>
            <option>GET</option>
            <option>POST</option>
            <option>PUT</option>
            <option>DELETE</option>
          </select>

          <input
            placeholder="Enter URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />

          <button onClick={handleSend}>Send</button>

          <button
            onClick={() => saveRequest(0, { url, method, headers, body })}
          >
            Save
          </button>
        </div>

        {/* AUTH */}
        <div className="auth">
          <select
            onChange={(e) => setAuth({ ...auth, type: e.target.value })}
          >
            <option value="none">No Auth</option>
            <option value="bearer">Bearer</option>
            <option value="apiKey">API Key</option>
          </select>

          {auth.type === "bearer" && (
            <input
              placeholder="Token"
              onChange={(e) =>
                setAuth({ ...auth, token: e.target.value })
              }
            />
          )}

          {auth.type === "apiKey" && (
            <>
              <input
                placeholder="Key"
                onChange={(e) =>
                  setAuth({ ...auth, key: e.target.value })
                }
              />
              <input
                placeholder="Value"
                onChange={(e) =>
                  setAuth({ ...auth, value: e.target.value })
                }
              />
            </>
          )}

          {/* THROTTLE */}
          <select onChange={(e) => setThrottle(e.target.value)}>
            <option value="no-limit">No Limit</option>
            <option value="2g">2G</option>
            <option value="3g">3G</option>
            <option value="4g">4G</option>
            <option value="5g">5G</option>
          </select>
        </div>

        {/* TEST SCRIPT */}
        <div className="tab-content">
          <textarea
            placeholder="pm.test('Status is 200', () => { pm.expect(pm.response.code).toBe(200); });"
            onChange={(e) => setTests(e.target.value)}
          />
        </div>

        {/* RESPONSE */}
        <div className="response">
          {response && (
            <>
              <div>
                Status: {response.status} | Time: {response.time} ms | Size:{" "}
                {response.size}
              </div>

              <pre>{response.data}</pre>

              <h4>Tests</h4>
              {response.tests.map((t, i) => (
                <div key={i}>
                  {t.name}: {t.status}
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}