import React from "react";

export default function SidebarPanel({ collections = [], onSelect }) {
  return (
    <div className="sidebar-panel">
      <h3>📁 Collections</h3>

      {collections.length === 0 && (
        <p style={{ color: "#888" }}>No collections</p>
      )}

      {collections.map((col, i) => (
        <div key={i} className="collection-item">
          <div style={{ fontWeight: "bold" }}>{col.name}</div>

          {(col.requests || []).map((req, j) => (
            <div
              key={j}
              className="collection-item"
              style={{ marginLeft: 10 }}
              onClick={() => onSelect && onSelect(req)}
            >
              {req.method} {req.url}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}