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
    addHistory
  } = useApiStore();

  const [tabs, setTabs] = useState([{ id: 1 }]);
  const [activeTab, setActiveTab] = useState(0);

  const [url, setUrl] = useState("");
  const [method, setMethod] = useState("GET");

  const [params, setParams] = useState([{ key: "", value: "" }]);
  const [headers, setHeaders] = useState([{ key: "", value: "" }]);
  const [body, setBody] = useState("");

  const [activePanel, setActivePanel] = useState("params");

  const [response, setResponse] = useState(null);
  const [history, setHistory] = useState([]);

  // 🔥 SEND REQUEST
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

    const res = await sendRequest({
      url: finalUrl,
      method,
      headers: headerObj,
      body
    });

    setResponse(res);

    const entry = { url, method };
    setHistory((prev) => [entry, ...prev]);
    addHistory(entry);
  };

  return (
    <div className="full-layout">

      {/* SIDEBAR */}
      <div className="sidebar-panel">

        <button onClick={() => addCollection("New Collection")}>
          + Collection
        </button>

        <h3>Collections</h3>

        {collections.map((col, ci) => (
          <div key={ci} className="collection-item">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <b>{col.name}</b>
              <button onClick={() => deleteRequest(ci, 0)}>🗑</button>
            </div>
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

        {/* TABS */}
        <div className="tab-bar">
          {tabs.map((t, i) => (
            <div
              key={i}
              className={i === activeTab ? "tab active" : "tab"}
              onClick={() => setActiveTab(i)}
            >
              Tab {i + 1}
              <span
                onClick={(e) => {
                  e.stopPropagation();
                  const newTabs = tabs.filter((_, idx) => idx !== i);
                  setTabs(newTabs);
                  setActiveTab(0);
                }}
                style={{ marginLeft: 8, color: "red", cursor: "pointer" }}
              >
                ✕
              </span>
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
            onClick={() =>
              saveRequest(0, { url, method, headers, body })
            }
          >
            Save
          </button>
        </div>

        {/* TABS PANEL */}
        <div className="tabs">
          <button
            className={activePanel === "params" ? "active" : ""}
            onClick={() => setActivePanel("params")}
          >
            Params
          </button>
          <button
            className={activePanel === "headers" ? "active" : ""}
            onClick={() => setActivePanel("headers")}
          >
            Headers
          </button>
          <button
            className={activePanel === "body" ? "active" : ""}
            onClick={() => setActivePanel("body")}
          >
            Body
          </button>
        </div>

        {/* PARAMS */}
        {activePanel === "params" && (
          <div className="tab-content">
            {params.map((p, i) => (
              <div className="row" key={i}>
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
            <button
              className="add-btn"
              onClick={() => setParams([...params, { key: "", value: "" }])}
            >
              + Add
            </button>
          </div>
        )}

        {/* HEADERS */}
        {activePanel === "headers" && (
          <div className="tab-content">
            {headers.map((h, i) => (
              <div className="row" key={i}>
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
            <button
              className="add-btn"
              onClick={() => setHeaders([...headers, { key: "", value: "" }])}
            >
              + Add
            </button>
          </div>
        )}

        {/* BODY */}
        {activePanel === "body" && (
          <div className="tab-content">
            <textarea
              placeholder="Raw JSON body"
              onChange={(e) => setBody(e.target.value)}
            />
          </div>
        )}

        {/* RESPONSE */}
        <div className="response">
          {response && (
            <>
              <div>
                Status: {response.status} | Time: {response.time} ms | Size: {response.size}
              </div>
              <pre>{response.data}</pre>
            </>
          )}
        </div>
      </div>
    </div>
  );
}