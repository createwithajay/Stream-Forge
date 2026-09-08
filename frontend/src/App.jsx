import { useEffect, useState } from "react";
import "./App.css";
import WebRTCPlayer from "./WebRTCPlayer";

function App() {
  const [metrics, setMetrics] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [streams, setStreams] = useState([]);
  const [pipeline, setPipeline] = useState(null);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [systemOnline, setSystemOnline] = useState(false);

  // Engine Management State
  const [engines, setEngines] = useState([]);
  const [activeEngine, setActiveEngine] = useState(null);
  const [engineFile, setEngineFile] = useState(null);
  const [engineMessage, setEngineMessage] = useState("");
  const [engineLoading, setEngineLoading] = useState(false);

  // Fetch dashboard data
  async function fetchDashboardData() {
    try {
      const [
        metricsResponse,
        camerasResponse,
        pipelineResponse,
        streamsResponse,
      ] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/metrics"),
        fetch("http://127.0.0.1:8000/api/cameras"),
        fetch("http://127.0.0.1:8000/api/pipeline"),
        fetch("http://127.0.0.1:8000/api/streams"),
      ]);

      if (
        !metricsResponse.ok ||
        !camerasResponse.ok ||
        !pipelineResponse.ok ||
        !streamsResponse.ok
      ) {
        throw new Error("Failed to fetch dashboard data");
      }

      const metricsData = await metricsResponse.json();
      const camerasData = await camerasResponse.json();
      const pipelineData = await pipelineResponse.json();
      const streamsData = await streamsResponse.json();

      setMetrics(metricsData);
      setCameras(camerasData.cameras || []);
      setPipeline(pipelineData);
      setStreams(streamsData.streams || []);

      setError("");
      setSystemOnline(true);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      setSystemOnline(false);
      setError("Backend connection lost. Retrying automatically...");
    }
  }

  // Fetch TensorRT engines
  async function fetchEngines() {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/engines"
      );

      if (!response.ok) {
        throw new Error("Failed to fetch engines");
      }

      const data = await response.json();

      setEngines(data.engines || []);
      setActiveEngine(data.active_engine || null);
    } catch (err) {
      console.error("Engine fetch error:", err);
    }
  }

  // Upload TensorRT engine
  async function uploadEngine() {
    if (!engineFile) {
      setEngineMessage("Please select an engine file first.");
      return;
    }

    setEngineLoading(true);
    setEngineMessage("");

    try {
      const formData = new FormData();
      formData.append("file", engineFile);

      const response = await fetch(
        "http://127.0.0.1:8000/api/engines/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Engine upload failed"
        );
      }

      setEngineMessage(
        `Uploaded successfully: ${data.original_name}`
      );

      setEngineFile(null);

      await fetchEngines();
    } catch (err) {
      console.error("Engine upload error:", err);
      setEngineMessage(err.message);
    } finally {
      setEngineLoading(false);
    }
  }

  // Switch active TensorRT engine
  async function switchEngine(engineName) {
    setEngineLoading(true);
    setEngineMessage("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/engines/switch",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            engine_name: engineName,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Engine switch failed"
        );
      }

      setActiveEngine(data.active_engine);

      setEngineMessage(
        `Active engine: ${data.active_engine}`
      );

      await fetchEngines();
    } catch (err) {
      console.error("Engine switch error:", err);
      setEngineMessage(err.message);
    } finally {
      setEngineLoading(false);
    }
  }

  // Automatic dashboard refresh
  useEffect(() => {
    fetchDashboardData();
    fetchEngines();

    const interval = setInterval(() => {
      fetchDashboardData();
      fetchEngines();
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

          {systemOnline
            ? "System Online"
            : "System Offline"}
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
          Last updated:{" "}
          {lastUpdated.toLocaleTimeString()}
        </p>
      )}

      {/* Metrics */}
      {metrics && (
        <section className="metrics-grid">

          {/* CPU */}
          <div className="metric-card">
            <h3>CPU Usage</h3>

            <div className="metric-value">
              {metrics.cpu_usage.toFixed(1)}%
            </div>

            <span>
              Processor utilization
            </span>
          </div>

          {/* GPU */}
          <div className="metric-card">
            <h3>GPU Usage</h3>

            <div className="metric-value">
              {metrics.gpu_usage}%
            </div>

            <span>
              {metrics.gpu_metrics_source ===
              "fallback"
                ? "Telemetry unavailable (fallback)"
                : "Live GPU utilization"}
            </span>

            <div className="metric-subvalue">
              Decoder:{" "}
              {metrics.decoder_utilization !==
                null &&
              metrics.decoder_utilization !==
                undefined
                ? `${metrics.decoder_utilization}%`
                : "Unavailable"}
            </div>
          </div>

          {/* Memory */}
          <div className="metric-card">
            <h3>Memory Usage</h3>

            <div className="metric-value">
              {metrics.memory_usage.toFixed(1)}%
            </div>

            <span>
              System memory
            </span>
          </div>

          {/* FPS */}
          <div className="metric-card">
            <h3>FPS</h3>

            <div className="metric-value">
              {metrics.fps}
            </div>

            <span>
              Frames per second
            </span>
          </div>

          {/* Inference Latency */}
          <div className="metric-card">
            <h3>Inference Latency</h3>

            <div className="metric-value">
              {metrics.inference_latency_ms} ms
            </div>

            <span>
              Simulated inference latency
            </span>
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
              <span>
                {pipeline.pipeline.video_input}
              </span>
            </div>

            <div className="pipeline-card">
              <h3>DeepStream</h3>
              <span>
                {pipeline.pipeline.deepstream}
              </span>
            </div>

            <div className="pipeline-card">
              <h3>TensorRT Inference</h3>
              <span>
                {pipeline.pipeline.tensorrt_inference}
              </span>
            </div>

            <div className="pipeline-card">
              <h3>Output</h3>
              <span>
                {pipeline.pipeline.output}
              </span>
            </div>

          </div>
        </section>
      )}

      {/* TensorRT Engine Management */}
      <section className="camera-section">

        <div className="section-title">
          <h2>
            TensorRT Engine Management
          </h2>

          <span>
            {activeEngine
              ? `Active: ${activeEngine}`
              : "No active engine"}
          </span>
        </div>

        <div className="engine-management">

          {/* Upload */}
          <div className="engine-upload">

            <h3>
              Upload TensorRT Engine
            </h3>

            <p>
              Supported formats: .engine, .plan
            </p>

            <input
              type="file"
              accept=".engine,.plan"
              onChange={(event) =>
                setEngineFile(
                  event.target.files[0] || null
                )
              }
            />

            <button
              onClick={uploadEngine}
              disabled={
                !engineFile || engineLoading
              }
            >
              {engineLoading
                ? "Processing..."
                : "Upload Engine"}
            </button>

          </div>

          {/* Engine List */}
          <div className="engine-list">

            <h3>
              Available Engines
            </h3>

            {engines.length === 0 ? (
              <p>
                No TensorRT engines uploaded.
              </p>
            ) : (
              engines.map((engine) => (
                <div
                  className="engine-card"
                  key={engine.engine_name}
                >

                  <div>
                    <strong>
                      {engine.engine_name}
                    </strong>

                    <p>
                      Size: {engine.size_mb} MB
                    </p>

                    <span
                      className={
                        engine.active
                          ? "live"
                          : "offline"
                      }
                    >
                      ●{" "}
                      {engine.active
                        ? "ACTIVE"
                        : "AVAILABLE"}
                    </span>
                  </div>

                  <button
                    onClick={() =>
                      switchEngine(
                        engine.engine_name
                      )
                    }
                    disabled={
                      engine.active ||
                      engineLoading
                    }
                  >
                    {engine.active
                      ? "Active"
                      : "Switch"}
                  </button>

                </div>
              ))
            )}

          </div>

        </div>

        {engineMessage && (
          <div className="engine-message">
            {engineMessage}
          </div>
        )}

        <div className="simulation-notice">
          ⚠ TensorRT execution mode: SIMULATED
        </div>

      </section>

      {/* WebRTC Test Stream */}
      <section className="camera-section">

        <div className="section-title">
          <h2>
            WebRTC Video Stream
          </h2>

          <span>
            Real-time Test Pipeline
          </span>
        </div>

        <WebRTCPlayer />

      </section>

      {/* Multi-Stream Telemetry */}
      <section className="camera-section">

        <div className="section-title">
          <h2>
            Multi-Stream Telemetry
          </h2>

          <span>
            Asyncio Stream Manager
          </span>
        </div>

        <div className="camera-grid">

          {streams.map((stream) => (
            <div
              className="camera-card"
              key={stream.stream_id}
            >

              <div className="camera-header">

                <h3>
                  {stream.name}
                </h3>

                <span
                  className={
                    stream.status === "RUNNING"
                      ? "live"
                      : "offline"
                  }
                >
                  ● {stream.status}
                </span>

              </div>

              <div
                className={
                  stream.status === "RUNNING"
                    ? "video-placeholder"
                    : "video-placeholder offline-video"
                }
              >
                {stream.status === "RUNNING"
                  ? "Asyncio Stream Active"
                  : "Stream Offline"}
              </div>

              <div className="camera-info">

                <span>
                  {stream.fps} FPS
                </span>

                <span>•</span>

                <span>
                  {stream.frames_processed} frames
                </span>

              </div>

            </div>
          ))}

        </div>

      </section>

      {/* Camera Monitoring */}
      <section className="camera-section">

        <div className="section-title">
          <h2>
            Camera Monitoring
          </h2>

          <span>
            VisionEdge Pipeline
          </span>
        </div>

        <div className="camera-grid">

          {cameras.map((camera) => (
            <div
              className="camera-card"
              key={camera.id}
            >

              <div className="camera-header">

                <h3>
                  {camera.name}
                </h3>

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
                  Resolution:{" "}
                  {camera.resolution || "--"}
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