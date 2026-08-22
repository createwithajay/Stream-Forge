import CameraCard from "./CameraCard";

function CameraGrid() {
  const cameras = [
    {
      name: "Camera 01",
      status: "LIVE",
      fps: 58,
      objects: 14,
    },
    {
      name: "Camera 02",
      status: "LIVE",
      fps: 60,
      objects: 21,
    },
    {
      name: "Camera 03",
      status: "LIVE",
      fps: 57,
      objects: 9,
    },
    {
      name: "Camera 04",
      status: "OFFLINE",
      fps: "--",
      objects: "--",
    },
  ];

  return (
    <section className="camera-section">

      <div className="section-title">
        <h2>Camera Streams</h2>
        <span>{cameras.length} Streams</span>
      </div>

      <div className="camera-grid">
        {cameras.map((camera) => (
          <CameraCard
            key={camera.name}
            name={camera.name}
            status={camera.status}
            fps={camera.fps}
            objects={camera.objects}
          />
        ))}
      </div>

    </section>
  );
}

export default CameraGrid;