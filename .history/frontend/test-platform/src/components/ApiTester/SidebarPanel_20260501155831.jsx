import { useApiStore } from "../../store/useApiStore";

export default function SidebarPanel({ loadRequest }) {
  const { collections, history } = useApiStore();

  return (
    <div className="sidepanel">
      <h3>Collections</h3>
      {collections.map((c) => (
        <div key={c.id} className="item" onClick={() => loadRequest(c)}>
          {c.method} {c.url}
        </div>
      ))}

      <h3>History</h3>
      {history.map((h) => (
        <div key={h.id} className="item" onClick={() => loadRequest(h)}>
          {h.method} {h.url}
        </div>
      ))}
    </div>
  );
}