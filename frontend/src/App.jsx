import { useEffect, useState } from "react";

function App() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/metrics")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch metrics");
        }
        return response.json();
      })
      .then((data) => {
        setMetrics(data);
      })
      .catch((err) => {
        setError(err.message);
      });
  }, []);

  return (
    <div>
      <h1>VisionEdge Dashboard</h1>

      {error && <p>{error}</p>}

      {metrics && (
        <div>
          <p>CPU Usage: {metrics.cpu_usage}%</p>
          <p>GPU Usage: {metrics.gpu_usage}%</p>
          <p>Memory Usage: {metrics.memory_usage}%</p>
          <p>FPS: {metrics.fps}</p>
        </div>
      )}
    </div>
  );
}

export default App;