export default function Loading() {
  return (
    <div className="msg msg-assistant">
      <div className="loading">
        <span className="lumen">
          <span className="lumen-ring" />
          <span className="lumen-core" />
        </span>
        <span className="loading-label">searching the corpus…</span>
      </div>
    </div>
  );
}
