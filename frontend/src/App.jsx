import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");

  function fetchMetrics() {
    fetch("http://127.0.0.1:8000/api/metrics")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch metrics");
        }
        return response.json();
      })
      .then((data) => {
        setMetrics(data);
        setError("");
      })
      .catch((err) => {
        setError(err.message);
      });
  }

  useEffect(() => {
    fetchMetrics();

    const interval = setInterval(() => {
      fetchMetrics();
    }, 5000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="dashboard">

      <header className="header">
        <div>
          <h1>VisionEdge Dashboard</h1>
          <p>Edge AI Monitoring System</p>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          System Online
        </div>
      </header>

      {error && (
        <p style={{ color: "#ef4444" }}>
          {error}
        </p>
      )}

      {metrics && (
        <section className="metrics-grid">

          <div className="metric-card">
            <h3>CPU Usage</h3>
            <div className="metric-value">
              {metrics.cpu_usage}%
            </div>
            <span>Processor utilization</span>
          </div>

          <div className="metric-card">
            <h3>GPU Usage</h3>
            <div className="metric-value">
              {metrics.gpu_usage}%
            </div>
            <span>GPU utilization</span>
          </div>

          <div className="metric-card">
            <h3>Memory Usage</h3>
            <div className="metric-value">
              {metrics.memory_usage}%
            </div>
            <span>System memory</span>
          </div>

          <div className="metric-card">
            <h3>FPS</h3>
            <div className="metric-value">
              {metrics.fps}
            </div>
            <span>Frames per second</span>
          </div>

        </section>
      )}

      <section className="camera-section">

        <div className="section-title">
          <h2>Camera Monitoring</h2>
          <span>VisionEdge Pipeline</span>
        </div>

        <div className="camera-grid">

          <div className="camera-card">

            <div className="camera-header">
              <h3>Camera 01</h3>
              <span className="live">● LIVE</span>
            </div>

            <div className="video-placeholder">
              Video Stream
            </div>

            <div className="camera-info">
              <span>Resolution: 1080p</span>
              <span>{metrics?.fps || 0} FPS</span>
            </div>

          </div>

          <div className="camera-card">

            <div className="camera-header">
              <h3>Camera 02</h3>
              <span className="offline">● OFFLINE</span>
            </div>

            <div className="video-placeholder offline-video">
              Camera Offline
            </div>

            <div className="camera-info">
              <span>Resolution: --</span>
              <span>0 FPS</span>
            </div>

          </div>

        </div>

      </section>

    </div>
  );
}

export default App;