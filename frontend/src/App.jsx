import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [metrics, setMetrics] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [pipeline, setPipeline] = useState(null);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [systemOnline, setSystemOnline] = useState(false);

  async function fetchDashboardData() {
    try {
      const [metricsResponse, camerasResponse, pipelineResponse] =
        await Promise.all([
          fetch("http://127.0.0.1:8000/api/metrics"),
          fetch("http://127.0.0.1:8000/api/cameras"),
          fetch("http://127.0.0.1:8000/api/pipeline"),
        ]);

      if (
        !metricsResponse.ok ||
        !camerasResponse.ok ||
        !pipelineResponse.ok
      ) {
        throw new Error("Failed to fetch dashboard data");
      }

      const metricsData = await metricsResponse.json();
      const camerasData = await camerasResponse.json();
      const pipelineData = await pipelineResponse.json();

      setMetrics(metricsData);
      setCameras(camerasData.cameras);
      setPipeline(pipelineData);

      setError("");
      setSystemOnline(true);
      setLastUpdated(new Date());
    } catch (err) {
      setSystemOnline(false);
      setError(
        "Backend connection lost. Retrying automatically..."
      );
    }
  }

  useEffect(() => {
    fetchDashboardData();

    const interval = setInterval(() => {
      fetchDashboardData();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard">

      {/* Header */}
      <header className="header">
        <div>
          <h1>VisionEdge Dashboard</h1>
          <p>Edge AI Monitoring System</p>
        </div>

        <div className="system-status">
          <span
            className={
              systemOnline
                ? "status-dot"
                : "status-dot offline-dot"
            }
          ></span>

          {systemOnline ? "System Online" : "System Offline"}
        </div>
      </header>

      {/* Error Message */}
      {error && (
        <div className="error-message">
          <span>{error}</span>

          <button onClick={fetchDashboardData}>
            Retry Now
          </button>
        </div>
      )}

      {/* Last Updated */}
      {lastUpdated && (
        <p className="last-updated">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </p>
      )}

      {/* Metrics */}
      {metrics && (
        <section className="metrics-grid">

          <div className="metric-card">
            <h3>CPU Usage</h3>

            <div className="metric-value">
              {metrics.cpu_usage.toFixed(1)}%
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
              {metrics.memory_usage.toFixed(1)}%
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

      {/* Pipeline Status */}
      {pipeline && (
        <section className="pipeline-section">

          <div className="section-title">
            <h2>Pipeline Status</h2>

            <span
              className={
                pipeline.status === "RUNNING"
                  ? "pipeline-running"
                  : "pipeline-stopped"
              }
            >
              ● {pipeline.status}
            </span>
          </div>

          <div className="pipeline-grid">

            <div className="pipeline-card">
              <h3>Video Input</h3>
              <span>{pipeline.pipeline.video_input}</span>
            </div>

            <div className="pipeline-card">
              <h3>DeepStream</h3>
              <span>{pipeline.pipeline.deepstream}</span>
            </div>

            <div className="pipeline-card">
              <h3>TensorRT Inference</h3>
              <span>{pipeline.pipeline.tensorrt_inference}</span>
            </div>

            <div className="pipeline-card">
              <h3>Output</h3>
              <span>{pipeline.pipeline.output}</span>
            </div>

          </div>

        </section>
      )}

      {/* Camera Monitoring */}
      <section className="camera-section">

        <div className="section-title">
          <h2>Camera Monitoring</h2>
          <span>VisionEdge Pipeline</span>
        </div>

        <div className="camera-grid">

          {cameras.map((camera) => (
            <div className="camera-card" key={camera.id}>

              <div className="camera-header">
                <h3>{camera.name}</h3>

                <span
                  className={
                    camera.status === "LIVE"
                      ? "live"
                      : "offline"
                  }
                >
                  ● {camera.status}
                </span>
              </div>

              <div
                className={
                  camera.status === "LIVE"
                    ? "video-placeholder"
                    : "video-placeholder offline-video"
                }
              >
                {camera.status === "LIVE"
                  ? "Video Stream"
                  : "Camera Offline"}
              </div>

              <div className="camera-info">

                <span>
                  Resolution: {camera.resolution || "--"}
                </span>

                <span>•</span>

                <span>
                  {camera.fps || 0} FPS
                </span>

              </div>

            </div>
          ))}

        </div>

      </section>

    </div>
  );
}

export default App;