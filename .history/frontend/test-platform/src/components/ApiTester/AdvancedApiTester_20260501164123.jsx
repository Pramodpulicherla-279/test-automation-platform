import { useState } from "react";
import { useApiStore } from "../../store/useApiStore";
import { sendRequest } from "../../utils/requestExecutor";
import "./ApiTesterPro.css";

export default function AdvancedApiTester() {
  const {
    collections,
    addCollection,
    deleteCollection,
    saveRequest,
    history,
    addHistory
  } = useApiStore();

  const [selectedCollection, setSelectedCollection] = useState(0);

  const [url, setUrl] = useState("");
  const [method, setMethod] = useState("GET");

  const [params, setParams] = useState([{ key: "", value: "" }]);
  const [headers, setHeaders] = useState([{ key: "", value: "" }]);
  const [body, setBody] = useState("");

  const [activePanel, setActivePanel] = useState("params");

  const [response, setResponse] = useState(null);

  // ✅ NETWORK THROTTLING
  const throttles = {
    "No Limit": 0,
    "2G": 2000,
    "3G": 800,
    "4G": 200,
    "5G": 50
  };

  const [throttle, setThrottle] = useState("No Limit");

  const delay = (ms) => new Promise((res) => setTimeout(res, ms));

  const handleSend = async () => {
    let query = params
      .filter((p) => p.key)
      .map((p) => `${p.key}=${p.value}`)
      .join("&");

    const finalUrl = query ? `${url}?${query}` : url;

    const headerObj = {};
    headers.forEach((h) => {
      if (h.key) headerObj[h.key] = h.value;
    });

    await delay(throttles[throttle]);

    const res = await sendRequest({
      url: finalUrl,
      method,
      headers: headerObj,
      body
    });

    setResponse(res);
    addHistory({ url, method });
  };

  return (
    <div className="full-layout">

      {/* SIDEBAR */}
      <div className="sidebar-panel">

        <button onClick={() => addCollection("New Collection")}>
          + Collection
        </button>

        <h3>Collections</h3>

        {collections.map((col, i) => (
          <div
            key={i}
            className="collection-item"
            onClick={() => setSelectedCollection(i)}
          >
            <span>{col.name}</span>

            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteCollection(i);
              }}
            >
              🗑
            </button>
          </div>
        ))}

        <h3>History</h3>
        {history.map((h, i) => (
          <div key={i} className="collection-item">
            {h.method} {h.url}
          </div>
        ))}
      </div>

      {/* MAIN */}
      <div className="api-root">

        {/* TOP BAR */}
        <div className="topbar">
          <select value={method} onChange={(e) => setMethod(e.target.value)}>
            <option>GET</option>
            <option>POST</option>
          </select>

          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter URL"
          />

          {/* 🔥 THROTTLE */}
          <select value={throttle} onChange={(e) => setThrottle(e.target.value)}>
            {Object.keys(throttles).map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>

          <button onClick={handleSend}>Send</button>

          <button
            onClick={() =>
              saveRequest(selectedCollection, {
                url,
                method,
                params,
                headers,
                body
              })
            }
          >
            Save
          </button>
        </div>

        {/* PANELS */}
        <div className="tabs">
          <button onClick={() => setActivePanel("params")}>Params</button>
          <button onClick={() => setActivePanel("headers")}>Headers</button>
          <button onClick={() => setActivePanel("body")}>Body</button>
        </div>

        {activePanel === "params" && (
          <div>
            {params.map((p, i) => (
              <div key={i}>
                <input
                  placeholder="Key"
                  onChange={(e) => {
                    const copy = [...params];
                    copy[i].key = e.target.value;
                    setParams(copy);
                  }}
                />
                <input
                  placeholder="Value"
                  onChange={(e) => {
                    const copy = [...params];
                    copy[i].value = e.target.value;
                    setParams(copy);
                  }}
                />
              </div>
            ))}
          </div>
        )}

        {activePanel === "headers" && (
          <div>
            {headers.map((h, i) => (
              <div key={i}>
                <input
                  placeholder="Key"
                  onChange={(e) => {
                    const copy = [...headers];
                    copy[i].key = e.target.value;
                    setHeaders(copy);
                  }}
                />
                <input
                  placeholder="Value"
                  onChange={(e) => {
                    const copy = [...headers];
                    copy[i].value = e.target.value;
                    setHeaders(copy);
                  }}
                />
              </div>
            ))}
          </div>
        )}

        {activePanel === "body" && (
          <textarea
            placeholder="Raw JSON"
            onChange={(e) => setBody(e.target.value)}
          />
        )}

        {/* RESPONSE */}
        <div className="response">
          {response && (
            <>
              <div>
                Status: {response.status} | Time: {response.time} ms
              </div>
              <pre>{response.data}</pre>
            </>
          )}
        </div>
      </div>
    </div>
  );
}