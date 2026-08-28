from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Gauge, generate_latest
from fastapi.responses import Response
import psutil

app = FastAPI(
    title="VisionEdge API",
    description="Backend API for the VisionEdge Edge AI Monitoring System",
    version="1.0.0",
)

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Prometheus metrics
cpu_gauge = Gauge("visionedge_cpu_usage_percent", "CPU usage percentage")
memory_gauge = Gauge("visionedge_memory_usage_percent", "Memory usage percentage")
gpu_gauge = Gauge("visionedge_gpu_usage_percent", "GPU usage percentage")
fps_gauge = Gauge("visionedge_fps", "Video frames per second")

camera_requests = Counter(
    "visionedge_camera_requests_total",
    "Number of camera monitoring requests",
)


@app.get("/")
def root():
    return {
        "project": "VisionEdge",
        "status": "online",
        "message": "VisionEdge API is running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "visionedge-backend",
    }


@app.get("/api/metrics")
def get_metrics():
    cpu_usage = psutil.cpu_percent(interval=0.1)
    memory_usage = psutil.virtual_memory().percent

    # GPU value is currently simulated.
    # It can later be connected to NVIDIA GPU monitoring.
    gpu_usage = 62

    # FPS is currently simulated from the video pipeline.
    fps = 30

    # Update Prometheus metrics
    cpu_gauge.set(cpu_usage)
    memory_gauge.set(memory_usage)
    gpu_gauge.set(gpu_usage)
    fps_gauge.set(fps)

    return {
        "cpu_usage": cpu_usage,
        "gpu_usage": gpu_usage,
        "memory_usage": memory_usage,
        "fps": fps,
    }


@app.get("/api/cameras")
def get_cameras():
    camera_requests.inc()

    return {
        "cameras": [
            {
                "id": 1,
                "name": "Camera 01",
                "status": "LIVE",
                "resolution": "1080p",
                "fps": 30,
            },
            {
                "id": 2,
                "name": "Camera 02",
                "status": "OFFLINE",
                "resolution": None,
                "fps": 0,
            },
        ]
    }


@app.get("/metrics")
def prometheus_metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain",
    )