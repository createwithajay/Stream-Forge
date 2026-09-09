function CameraCard({ name, status, fps, objects }) {
  const isLive = status === "LIVE";

  return (
    <div className="camera-card">

      <div className="camera-header">
        <h3>{name}</h3>

        <span className={isLive ? "live" : "offline"}>
          ● {status}
        </span>
      </div>

      <div className={`video-placeholder ${!isLive ? "offline-video" : ""}`}>
        {isLive ? "Video Stream" : "Stream Offline"}
      </div>

      <div className="camera-info">
        <span>FPS: {fps}</span>
        <span>Objects: {objects}</span>
      </div>

    </div>
  );
}

export default CameraCard;