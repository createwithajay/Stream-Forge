from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    event_id: str
    source: str = "simulator"
    temperature: float = Field(..., ge=-100, le=200)
    timestamp: float


class WorkerView(BaseModel):
    worker_id: int
    pid: int | None
    alive: bool
    restarts: int
