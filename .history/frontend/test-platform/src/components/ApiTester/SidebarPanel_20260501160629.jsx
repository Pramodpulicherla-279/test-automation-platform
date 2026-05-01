import { useApiStore } from "../../store/useApiStore";

export default function SidebarPanel({ loadRequest }) {
  const { collections, history } = useApiStore();

  return (
    <div className="sidepanel">
      <h3>📁 Collections</h3>

      {collections.length === 0 && (
        <p className="empty">No saved APIs</p>
      )}

      {collections.map((c) => (
        <div
          key={c.id}
          className="item"
          onClick={() => loadRequest(c)}
        >
          <b>{c.method}</b> {c.url}
        </div>
      ))}

      <h3>🕘 History</h3>

      {history.length === 0 && (
        <p className="empty">No history</p>
      )}

      {history.map((h) => (
        <div
          key={h.id}
          className="item"
          onClick={() => loadRequest(h)}
        >
          <b>{h.method}</b> {h.url}
        </div>
      ))}
    </div>
  );
}