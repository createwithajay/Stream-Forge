from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    return {
        "cpu_usage": 45,
        "gpu_usage": 62,
        "memory_usage": 58,
        "fps": 30,
    }