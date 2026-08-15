"""
Stream-Forge :: Topology & Dashboard bridge (Role 5)

This FastAPI app is the bridge between the pipeline's real metrics
(Prometheus, or the other roles' services) and the React Flow dashboard.

Right now /api/topology returns SIMULATED load numbers so the frontend
team can build against a stable contract before Roles 1-4 have real
Prometheus exporters running. Swap `simulate_metrics()` for a real
`prometheus_client` scrape (see the REPLACE-ME block below) once Role 4
exposes /metrics endpoints.
"""

import random
import time
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json

app = FastAPI(title="Stream-Forge Topology Bridge")

# Dev CORS — lock this down to your actual dashboard origin before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Static topology: matches the 4-stage architecture from the brief ----
NODES = [
    {"id": "kafka", "label": "Kafka Ingestion", "role": "Role 1", "kind": "source"},
    {"id": "faust", "label": "Stream Topology (Faust/Bytewax)", "role": "Role 2", "kind": "process"},
    {"id": "rocksdb", "label": "State & Aggregation (RocksDB)", "role": "Role 3", "kind": "state"},
    {"id": "chaos", "label": "Reliability & Chaos", "role": "Role 4", "kind": "monitor"},
]

EDGES = [
    {"id": "e1", "source": "kafka", "target": "faust"},
    {"id": "e2", "source": "faust", "target": "rocksdb"},
    {"id": "e3", "source": "rocksdb", "target": "chaos"},
]

# Persistent simulated state so values drift smoothly instead of jumping randomly
_state = {n["id"]: {"throughput": random.uniform(2000, 8000), "latency_ms": random.uniform(5, 40)} for n in NODES}


def simulate_metrics():
    """Randomly walks throughput/latency per node and flags bottlenecks.

    REPLACE-ME: once Role 4's Prometheus exporters are live, swap this for:
        from prometheus_api_client import PrometheusConnect
        prom = PrometheusConnect(url="http://localhost:9090")
        throughput = prom.custom_query('rate(events_processed_total[1m])')
    """
    snapshot = []
    for node in NODES:
        s = _state[node["id"]]
        s["throughput"] = max(500, s["throughput"] + random.uniform(-800, 800))
        s["latency_ms"] = max(1, s["latency_ms"] + random.uniform(-5, 5))

        # occasional chaos spike to prove the dashboard reacts to it
        bottleneck = s["latency_ms"] > 35 or random.random() < 0.05

        snapshot.append({
            "id": node["id"],
            "label": node["label"],
            "role": node["role"],
            "kind": node["kind"],
            "throughput_eps": round(s["throughput"]),
            "latency_ms": round(s["latency_ms"], 1),
            "bottleneck": bool(bottleneck),
            "ts": time.time(),
        })
    return snapshot


@app.get("/api/topology")
def get_topology():
    """One-shot fetch: nodes, edges, and current metrics snapshot."""
    return {"nodes": simulate_metrics(), "edges": EDGES}


@app.get("/api/stream")
async def stream_metrics():
    """Server-Sent Events stream — the dashboard subscribes to this for live updates
    instead of polling. One event every 2 seconds."""
    async def event_generator():
        while True:
            payload = {"nodes": simulate_metrics(), "edges": EDGES}
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}
