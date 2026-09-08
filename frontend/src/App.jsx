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
  const [compilerStatus, setCompilerStatus] = useState(null);
  const [inferenceStatus, setInferenceStatus] = useState(null);
  const [memoryProfile, setMemoryProfile] = useState(null);
  const [performanceAudit, setPerformanceAudit] = useState(null);

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
  compilerResponse,
  inferenceResponse,
  memoryResponse,
  performanceResponse,
] = await Promise.all([
  fetch("http://127.0.0.1:8000/api/metrics"),
  fetch("http://127.0.0.1:8000/api/cameras"),
  fetch("http://127.0.0.1:8000/api/pipeline"),
  fetch("http://127.0.0.1:8000/api/streams"),
  fetch("http://127.0.0.1:8000/api/compiler/status"),
  fetch("http://127.0.0.1:8000/api/inference/status"),
  fetch("http://127.0.0.1:8000/api/memory/profile"),
  fetch("http://127.0.0.1:8000/api/performance/audit"),
]);

    if (
  !metricsResponse.ok ||
  !camerasResponse.ok ||
  !pipelineResponse.ok ||
  !streamsResponse.ok ||
  !compilerResponse.ok ||
  !inferenceResponse.ok ||
  !memoryResponse.ok ||
  !performanceResponse.ok
) {
        throw new Error("Failed to fetch dashboard data");
      }

      const metricsData = await metricsResponse.json();
      const camerasData = await camerasResponse.json();
      const pipelineData = await pipelineResponse.json();
      const streamsData = await streamsResponse.json();
      const compilerData = await compilerResponse.json();
      const memoryData = await memoryResponse.json();
      const performanceData = await performanceResponse.json();
      const inferenceData = await inferenceResponse.json();
      setInferenceStatus(inferenceData);

      setMetrics(metricsData);
      setCameras(camerasData.cameras || []);
      setPipeline(pipelineData);
      setStreams(streamsData.streams || []);
      setCompilerStatus(compilerData);
      setMemoryProfile(memoryData);
      setPerformanceAudit(performanceData);

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
        
        {/* Inference Pipeline */}
{inferenceStatus && (
  <section className="pipeline-section">

    <div className="section-title">
      <h2>Inference Pipeline</h2>

      <span className="pipeline-running">
        ● {inferenceStatus.pipeline.inference_mode}
      </span>
    </div>

    <div className="pipeline-grid">

      <div className="pipeline-card">
        <h3>Frames Processed</h3>
        <span>
          {inferenceStatus.pipeline.frames_processed}
        </span>
      </div>

      <div className="pipeline-card">
        <h3>Detections</h3>
        <span>
          {inferenceStatus.pipeline.detections}
        </span>
      </div>

      <div className="pipeline-card">
        <h3>Average FPS</h3>
        <span>
          {inferenceStatus.pipeline.average_fps}
        </span>
      </div>

      <div className="pipeline-card">
        <h3>Latency</h3>
        <span>
          {inferenceStatus.pipeline.average_latency_ms} ms
        </span>
      </div>

    </div>
  </section>
)}

       {/* Model Compiler Status */}
{compilerStatus && (
  <section className="camera-section">

    <div className="section-title">
      <h2>Model Compiler Status</h2>

      <span
        className={
          compilerStatus.ready
            ? "pipeline-running"
            : "pipeline-stopped"
        }
      >
        ● {compilerStatus.mode}
      </span>
    </div>

    <div className="pipeline-grid">

      <div className="pipeline-card">
        <h3>Compilation</h3>
        <span>
          {compilerStatus.ready
            ? "READY"
            : "SIMULATED"}
        </span>
      </div>

      <div className="pipeline-card">
        <h3>PyTorch</h3>
        <span>
          {compilerStatus.hardware.pytorch
            ? "AVAILABLE"
            : "NOT AVAILABLE"}
        </span>
      </div>

      <div className="pipeline-card">
        <h3>ONNX</h3>
        <span>
          {compilerStatus.hardware.onnx
            ? "AVAILABLE"
            : "NOT AVAILABLE"}
        </span>
      </div>

      <div className="pipeline-card">
        <h3>TensorRT</h3>
        <span>
          {compilerStatus.hardware.tensorrt
            ? "AVAILABLE"
            : "NOT AVAILABLE"}
        </span>
      </div>

      <div className="pipeline-card">
        <h3>CUDA / NVIDIA</h3>
        <span>
          {compilerStatus.hardware.cuda
            ? "AVAILABLE"
            : "NOT AVAILABLE"}
        </span>
      </div>

      <div className="pipeline-card">
        <h3>CuPy</h3>
        <span>
          {compilerStatus.hardware.cupy
            ? "AVAILABLE"
            : "NOT AVAILABLE"}
        </span>
      </div>

    </div>

    {!compilerStatus.ready && (
      <div className="simulation-notice">
        ⚠ Real TensorRT compilation requires the NVIDIA/CUDA
        environment. Current compiler mode is SIMULATED.
      </div>
    )}

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

       {/* Performance Audit */}
<section className="camera-section">

  <div className="section-title">
    <h2>
      Performance Audit
    </h2>

    <span>
      TensorRT Benchmark
    </span>
  </div>

  {performanceAudit && (
    <div className="camera-grid">

      <div className="camera-card">
        <div className="camera-header">
          <h3>Inference Performance</h3>

          <span className="live">
            ● {performanceAudit.benchmark_mode}
          </span>
        </div>

        <div className="camera-info">
          <span>
            {performanceAudit.frames_tested} frames
          </span>

          <span>•</span>

          <span>
            {performanceAudit.average_fps} FPS
          </span>

          <span>•</span>

          <span>
            {performanceAudit.average_latency_ms} ms latency
          </span>
        </div>

      </div>

    </div>
  )}

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

      {/* Memory Profile */}
<section className="camera-section">

  <div className="section-title">
    <h2>Memory Profile</h2>
    <span>Runtime Memory Monitoring</span>
  </div>

  {memoryProfile && (
    <div className="camera-grid">

      <div className="camera-card">

        <div className="camera-header">
          <h3>Process Memory</h3>

          <span className="live">
            ● {memoryProfile.potential_memory_leak
              ? "CHECK"
              : "STABLE"}
          </span>
        </div>

        <div className="camera-info">

          <span>
            Before: {memoryProfile.process_memory_before_mb} MB
          </span>

          <span>•</span>

          <span>
            After: {memoryProfile.process_memory_after_mb} MB
          </span>

          <span>•</span>

          <span>
            Growth: {memoryProfile.process_memory_growth_mb} MB
          </span>

          <span>•</span>

          <span>
            GPU: {memoryProfile.gpu_available
              ? "Available"
              : "CPU Fallback"}
          </span>

        </div>

      </div>

    </div>
  )}

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

          <span>•</span>

          <span>
            {stream.detections} detections
          </span>

          <span>•</span>

          <span>
            {stream.processing_mode}
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