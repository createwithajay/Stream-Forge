from __future__ import annotations

import os
import random
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from .config import settings
from .models import TelemetryEvent
from .supervisor import WorkerSupervisor


BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(
    title="StreamForge Reliability Lab",
    version="1.0.0",
    description="A local reliability, performance and chaos engineering playground.",
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

supervisor = WorkerSupervisor(
    worker_count=settings.worker_count,
    queue_size=settings.queue_size,
    processing_delay_ms=settings.processing_delay_ms,
)

_generation_lock = threading.Lock()
_generation_running = False


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health():
    snapshot = supervisor.snapshot()
    alive = sum(1 for worker in snapshot["workers"] if worker["alive"])
    return {
        "status": "healthy" if alive == settings.worker_count else "degraded",
        "workers_alive": alive,
        "workers_expected": settings.worker_count,
        "queue_depth": snapshot["queue_depth"],
    }


@app.get("/api/status")
def status():
    return supervisor.snapshot()


@app.post("/api/events")
def ingest(event: TelemetryEvent):
    accepted = supervisor.submit(event.model_dump())
    if not accepted:
        raise HTTPException(status_code=503, detail="Event queue is full")
    return {"accepted": True, "event_id": event.event_id}


@app.post("/api/generate")
def generate(count: int = 1000):
    if count < 1 or count > 1_000_000:
        raise HTTPException(status_code=400, detail="count must be between 1 and 1,000,000")

    accepted = 0
    rejected = 0
    started = time.perf_counter()

    for _ in range(count):
        event = {
            "event_id": str(uuid.uuid4()),
            "source": "dashboard-generator",
            "temperature": random.uniform(-10, 55),
            "timestamp": time.time(),
        }
        if supervisor.submit(event):
            accepted += 1
        else:
            rejected += 1

    elapsed = time.perf_counter() - started
    return {
        "requested": count,
        "accepted": accepted,
        "rejected": rejected,
        "submission_rate": round(accepted / max(elapsed, 0.000001), 2),
    }


@app.post("/api/chaos/kill/{worker_id}")
def kill_worker(worker_id: int):
    if worker_id not in supervisor.workers:
        raise HTTPException(status_code=404, detail="Worker not found")

    killed = supervisor.stop_worker(worker_id)
    if not killed:
        raise HTTPException(status_code=409, detail="Worker is already stopped")

    return {
        "chaos_event": "worker_terminated",
        "worker_id": worker_id,
        "message": "Supervisor will detect the failure and restart the worker.",
    }


@app.post("/api/reset")
def reset():
    global supervisor
    supervisor.shutdown()
    supervisor = WorkerSupervisor(
        worker_count=settings.worker_count,
        queue_size=settings.queue_size,
        processing_delay_ms=settings.processing_delay_ms,
    )
    return {"status": "reset", "workers": settings.worker_count}


metrics_app = make_asgi_app()


@app.get("/metrics", include_in_schema=False)
async def metrics():
    from starlette.responses import Response
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
