import { useState } from "react";
import { useApiStore } from "../../store/useApiStore";

export default function SidebarPanel({ loadRequest, runRequest }) {
  const {
    collections,
    createCollection,
    addToCollection,
    deleteRequest,
    activeRequest,
  } = useApiStore();

  const [name, setName] = useState("");

  return (
    <div className="sidepanel">

      {/* CREATE COLLECTION */}
      <div className="section">
        <input
          placeholder="New Collection"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button onClick={() => {
          createCollection(name);
          setName("");
        }}>
          + Create
        </button>
      </div>

      {/* COLLECTION LIST */}
      {collections.map((c) => (
        <div key={c.id} className="collection">
          <h4>📁 {c.name}</h4>

          <button
            className="save-btn"
            onClick={() => addToCollection(c.id, activeRequest)}
          >
            Save API
          </button>

          {c.requests.map((r) => (
            <div key={r.id} className="item-row">
              <span
                className="item-text"
                onClick={() => loadRequest(r)}
              >
                {r.method} {r.url}
              </span>

              <div className="actions">
                <button onClick={() => runRequest(r)}>▶</button>
                <button onClick={() => deleteRequest(c.id, r.id)}>🗑</button>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}