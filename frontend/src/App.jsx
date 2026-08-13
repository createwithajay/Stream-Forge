import Header from "./components/Header";
import MetricCard from "./components/MetricCard";
import CameraGrid from "./components/CameraGrid";
import "./App.css";

function App() {
  const metrics = [
    {
      title: "GPU Usage",
      value: "72%",
      description: "Current utilization",
    },
    {
      title: "GPU Memory",
      value: "61%",
      description: "VRAM utilization",
    },
    {
      title: "Processing FPS",
      value: "58",
      description: "Frames per second",
    },
    {
      title: "Latency",
      value: "34 ms",
      description: "Pipeline latency",
    },
  ];

  return (
    <div className="dashboard">

      <Header />

      <section className="metrics-grid">
        {metrics.map((metric) => (
          <MetricCard
            key={metric.title}
            title={metric.title}
            value={metric.value}
            description={metric.description}
          />
        ))}
      </section>

      <CameraGrid />

    </div>
  );
}

export default App;