import asyncio
from pathlib import Path
import shutil
import uuid
import subprocess

from inference_pipeline import InferencePipeline
from fastapi import FastAPI, UploadFile, File, HTTPException
from video_decoder import decoder_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from performance_audit import TensorRTPerformanceAudit
from memory_profiler import MemoryProfiler
from video_decoder import validate_rtsp_source

from stream_manager import stream_manager
from model_compiler import (
    get_hardware_status,
    compilation_capability,
    get_nvidia_info,
)

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)

from av import VideoFrame
import numpy as np

from pydantic import BaseModel
from prometheus_client import (
    Counter,
    Gauge,
    generate_latest,
)
import psutil


# ==================================================
# TensorRT Engine Storage
# ==================================================

ENGINE_DIR = Path("engines")
ENGINE_DIR.mkdir(exist_ok=True)

active_engine = None


# ==================================================
# VisionEdge FastAPI Application
# ==================================================

app = FastAPI(
    title="VisionEdge API",
    description="Backend API for the VisionEdge Edge AI Monitoring System",
    version="1.0.0",
)


# ==================================================
# CORS Configuration
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# Prometheus Metrics
# ==================================================

cpu_gauge = Gauge(
    "visionedge_cpu_usage_percent",
    "CPU usage percentage",
)

memory_gauge = Gauge(
    "visionedge_memory_usage_percent",
    "Memory usage percentage",
)

gpu_gauge = Gauge(
    "visionedge_gpu_usage_percent",
    "GPU usage percentage",
)

fps_gauge = Gauge(
    "visionedge_fps",
    "Video frames per second",
)

inference_latency_gauge = Gauge(
    "visionedge_inference_latency_ms",
    "Inference processing latency in milliseconds",
)

camera_requests = Counter(
    "visionedge_camera_requests_total",
    "Number of camera monitoring requests",
)


# ==================================================
# Root Endpoint
# ==================================================

@app.get("/")
def root():
    return {
        "project": "VisionEdge",
        "status": "online",
        "message": "VisionEdge API is running",
    }


# ==================================================
# Health Check
# ==================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "visionedge-backend",
    }


# ==================================================
# Model Compiler Status
# ==================================================

@app.get("/api/compiler/status")
def compiler_status():
    capability = compilation_capability()

    return {
        "compiler": "VisionEdge Model Compiler",
        "mode": capability["mode"],
        "ready": capability["ready"],
        "hardware": get_hardware_status(),
        "nvidia": get_nvidia_info(),
        "missing_components": capability["missing_components"],
    }


# ==================================================
# GPU Metrics
# ==================================================

def get_gpu_metrics():
    """
    Try to collect NVIDIA GPU metrics using nvidia-smi.

    If NVIDIA GPU telemetry is unavailable, return a clearly
    labeled fallback value.
    """

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )

        if result.returncode == 0 and result.stdout.strip():

            gpu_usage, memory_used, memory_total = map(
                float,
                result.stdout.strip().split(","),
            )

            gpu_memory_percent = (
                (memory_used / memory_total) * 100
                if memory_total > 0
                else 0
            )

            return {
                "gpu_usage": gpu_usage,
                "gpu_memory_used_mb": memory_used,
                "gpu_memory_total_mb": memory_total,
                "gpu_memory_percent": round(
                    gpu_memory_percent,
                    2,
                ),
                "decoder_utilization": None,
                "source": "nvidia-smi",
            }

    except Exception:
        pass

    # NVIDIA telemetry unavailable on this machine.
    return {
        "gpu_usage": 62,
        "gpu_memory_used_mb": None,
        "gpu_memory_total_mb": None,
        "gpu_memory_percent": None,
        "decoder_utilization": None,
        "source": "fallback",
    }


# ==================================================
# System Metrics
# ==================================================

@app.get("/api/metrics")
def get_metrics():

    # Real CPU and memory metrics
    cpu_usage = psutil.cpu_percent(interval=0.1)
    memory_usage = psutil.virtual_memory().percent

    # GPU metrics
    gpu_metrics = get_gpu_metrics()

    # Currently simulated until real video pipeline exists
    fps = 30

    # Currently simulated until real TensorRT inference exists
    inference_latency = 12.5

    # Update Prometheus metrics
    cpu_gauge.set(cpu_usage)
    memory_gauge.set(memory_usage)
    gpu_gauge.set(gpu_metrics["gpu_usage"])
    fps_gauge.set(fps)
    inference_latency_gauge.set(inference_latency)

    return {
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,

        "gpu_usage": gpu_metrics["gpu_usage"],

        "gpu_memory_used_mb": gpu_metrics[
            "gpu_memory_used_mb"
        ],

        "gpu_memory_total_mb": gpu_metrics[
            "gpu_memory_total_mb"
        ],

        "gpu_memory_percent": gpu_metrics[
            "gpu_memory_percent"
        ],

        "decoder_utilization": gpu_metrics[
            "decoder_utilization"
        ],

        "fps": fps,

        "inference_latency_ms": inference_latency,

        "gpu_metrics_source": gpu_metrics[
            "source"
        ],
    }


# ==================================================
# Pipeline Status
# ==================================================

@app.get("/api/pipeline")
def get_pipeline_status():

    return {
        "pipeline": {
            "video_input": "ACTIVE",
            "deepstream": "NOT_AVAILABLE",
            "tensorrt_inference": "SIMULATED",
            "output": "ACTIVE",
        },
        "status": "RUNNING",
    }


# ==================================================
# Camera Monitoring
# ==================================================

@app.get("/api/cameras")
def get_cameras():

    camera_requests.inc()

    cameras = [
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
            "status": "LIVE",
            "resolution": "1080p",
            "fps": 30,
        },
        {
            "id": 3,
            "name": "Camera 03",
            "status": "LIVE",
            "resolution": "720p",
            "fps": 25,
        },
        {
            "id": 4,
            "name": "Camera 04",
            "status": "OFFLINE",
            "resolution": None,
            "fps": 0,
        },
    ]

    # Per-stream telemetry
    for camera in cameras:
        camera["telemetry"] = {
            "fps": camera["fps"],
            "stream_status": camera["status"],
        }

    return {
        "cameras": cameras,
        "stream_count": len(cameras),
        "active_streams": sum(
            1
            for camera in cameras
            if camera["status"] == "LIVE"
        ),
    }


# ==================================================
# Prometheus Endpoint
# ==================================================

@app.get("/metrics")
def prometheus_metrics():

    return Response(
        content=generate_latest(),
        media_type="text/plain",
    )


# ==================================================
# WebRTC Test Video Track
# ==================================================

class TestVideoTrack(VideoStreamTrack):

    def __init__(self):
        super().__init__()
        self.counter = 0

    async def recv(self):

        pts, time_base = await self.next_timestamp()

        width = 640
        height = 360

        # Create black frame
        frame = np.zeros(
            (height, width, 3),
            dtype=np.uint8,
        )

        # Moving green test rectangle
        x = (
            self.counter * 5
        ) % (
            width - 100
        )

        frame[
            100:200,
            x:x + 100
        ] = [0, 255, 0]

        # Convert NumPy frame to PyAV frame
        video_frame = VideoFrame.from_ndarray(
            frame,
            format="bgr24",
        )

        video_frame.pts = pts
        video_frame.time_base = time_base

        self.counter += 1

        return video_frame


# ==================================================
# WebRTC Offer Model
# ==================================================

class WebRTCOffer(BaseModel):

    sdp: str
    type: str


# ==================================================
# WebRTC Offer Endpoint
# ==================================================

@app.post("/api/webrtc/offer")
async def webrtc_offer(
    offer: WebRTCOffer,
):

    peer_connection = RTCPeerConnection()

    peer_connection.addTrack(
        TestVideoTrack()
    )

    remote_description = RTCSessionDescription(
        sdp=offer.sdp,
        type=offer.type,
    )

    await peer_connection.setRemoteDescription(
        remote_description
    )

    answer = await peer_connection.createAnswer()

    await peer_connection.setLocalDescription(
        answer
    )

    return {
        "sdp": peer_connection.localDescription.sdp,
        "type": peer_connection.localDescription.type,
    }


# ==================================================
# Multi-Stream Asyncio Monitoring
# ==================================================

@app.get("/api/streams")
def get_streams():

    return {
        "streams": stream_manager.get_streams(),
        "stream_count": len(stream_manager.streams),
        "active_streams": len(stream_manager.tasks),
    }


# ==================================================
# Start Multi-Stream Asyncio Processing
# ==================================================

@app.on_event("startup")
async def start_streams():

    # Start the three active camera streams
    await stream_manager.start_stream(1)
    await stream_manager.start_stream(2)
    await stream_manager.start_stream(3)

    # Camera 04 intentionally remains offline


# ==================================================
# TensorRT Engine Upload
# ==================================================

@app.post("/api/engines/upload")
async def upload_engine(
    file: UploadFile = File(...),
):
    """Upload a TensorRT engine file."""

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in {".engine", ".plan"}:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only .engine and .plan TensorRT files "
                "are supported"
            ),
        )

    safe_name = (
        f"{uuid.uuid4().hex}_"
        f"{Path(file.filename).name}"
    )

    destination = ENGINE_DIR / safe_name

    with destination.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
        )

    return {
        "status": "uploaded",
        "engine_name": safe_name,
        "original_name": file.filename,
        "execution_mode": "SIMULATED",
        "message": (
            "Engine uploaded successfully. "
            "TensorRT execution is currently simulated."
        ),
    }


# ==================================================
# List TensorRT Engines
# ==================================================

@app.get("/api/engines")
def list_engines():
    """List uploaded TensorRT engine files."""

    engines = []

    for engine_file in ENGINE_DIR.iterdir():

        if (
            engine_file.is_file()
            and engine_file.suffix.lower()
            in {".engine", ".plan"}
        ):

            engines.append(
                {
                    "engine_name": engine_file.name,
                    "size_mb": round(
                        engine_file.stat().st_size
                        / (1024 * 1024),
                        2,
                    ),
                    "active": (
                        engine_file.name
                        == active_engine
                    ),
                }
            )

    return {
        "engines": engines,
        "engine_count": len(engines),
        "active_engine": active_engine,
        "execution_mode": "SIMULATED",
    }


# ==================================================
# Engine Switch Request
# ==================================================

class EngineSwitchRequest(BaseModel):

    engine_name: str


# ==================================================
# Switch Active TensorRT Engine
# ==================================================

@app.post("/api/engines/switch")
def switch_engine(
    request: EngineSwitchRequest,
):
    """Switch the active TensorRT engine."""

    global active_engine

    engine_path = (
        ENGINE_DIR / request.engine_name
    )

    if not engine_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Engine file not found",
        )

    if engine_path.suffix.lower() not in {
        ".engine",
        ".plan",
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid TensorRT engine file",
        )

    active_engine = engine_path.name

    return {
        "status": "switched",
        "active_engine": active_engine,
        "execution_mode": "SIMULATED",
        "message": (
            "Active TensorRT engine changed successfully."
        ),
    }
@app.get("/api/decoder/status")
def decoder_status_api():
    return decoder_status()

@app.get("/api/inference/status")
def inference_status():
    pipeline = InferencePipeline(
        source="mock://camera",
        max_frames=30,
    )

    stats = pipeline.run()

    return {
        "pipeline": pipeline.status(),
        "results": {
            "frames_processed": stats.frames_processed,
            "detections": stats.detections,
            "elapsed_seconds": stats.elapsed_seconds,
            "average_fps": stats.average_fps,
            "average_latency_ms": stats.average_latency_ms,
        },
    }
@app.get("/api/memory/profile")
def memory_profile():
    profiler = MemoryProfiler()
    return profiler.profile(3)

@app.get("/api/performance/audit")
def performance_audit():
    audit = TensorRTPerformanceAudit(frames=100)
    result = audit.run()

    return {
        "frames_tested": result.frames,
        "total_time_seconds": result.total_time_seconds,
        "average_fps": result.average_fps,
        "average_latency_ms": result.average_latency_ms,
        "min_latency_ms": result.min_latency_ms,
        "max_latency_ms": result.max_latency_ms,
        "inference_mode": result.inference_mode,
        "benchmark_mode": (
            "REAL_TENSORRT"
            if result.inference_mode == "REAL_TENSORRT"
            else "SIMULATED_SOFTWARE"
        ),
    }
@app.get("/api/rtsp/validate")
def rtsp_validate(source: str):
    return validate_rtsp_source(source)
