import { useApiStore } from "../../store/useApiStore";

export default function SidebarPanel({ loadRequest }) {
  const { collections, history } = useApiStore();

  return (
    <div className="sidepanel">
      <div className="section">
        <h3>📁 Collections</h3>
        {collections.length === 0 && <p className="empty">No saved APIs</p>}

        {collections.map((c) => (
          <div
            key={c.id}
            className="item"
            onClick={() => loadRequest(c)}
          >
            <span className="method">{c.method}</span>
            <span className="url">{c.url}</span>
          </div>
        ))}
      </div>

      <div className="section">
        <h3>🕘 History</h3>
        {history.length === 0 && <p className="empty">No history</p>}

        {history.map((h) => (
          <div
            key={h.id}
            className="item"
            onClick={() => loadRequest(h)}
          >
            <span className="method">{h.method}</span>
            <span className="url">{h.url}</span>
          </div>
        ))}
      </div>
    </div>
  );
}