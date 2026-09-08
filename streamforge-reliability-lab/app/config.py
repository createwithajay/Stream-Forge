from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    worker_count: int = int(os.getenv("STREAMFORGE_WORKERS", "4"))
    queue_size: int = int(os.getenv("STREAMFORGE_QUEUE_SIZE", "50000"))
    processing_delay_ms: float = float(os.getenv("STREAMFORGE_PROCESSING_DELAY_MS", "0.2"))


settings = Settings()
