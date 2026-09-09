"""
starts the /metrics http server for prometheus to scrape.

run: python -m metrics_exporter.exporter

includes a fake traffic generator (simulate_pipeline) so there's something
to look at before the real pipeline is hooked up. rip that out once
record_event()/record_inflow() are being called from the actual code.
"""

import random
import threading
import time

from prometheus_client import start_http_server

from .anomaly import AnomalyDetector
from .backpressure import RateTracker, update_derived_metrics
from .metrics import (
    EVENTS_FAILED,
    EVENTS_PROCESSED,
    EXPORTER_UP,
    PROCESSING_DURATION,
    PROCESSING_LAG,
    QUEUE_DEPTH,
    SCRAPE_DURATION,
)
from .slo import SLOTracker

STAGES = ["ingest", "transform", "enrich", "load"]

tracker = RateTracker(window_seconds=10.0)
anomaly_detector = AnomalyDetector()
slo_tracker = SLOTracker()
_queue_depths = {stage: 0 for stage in STAGES}
_lock = threading.Lock()


def record_event(stage: str, duration_seconds: float, success: bool = True, error_type: str = "none"):
    """call once per event processed at a stage"""
    with _lock:
        tracker.record_outflow(stage)
        PROCESSING_DURATION.labels(stage=stage).observe(duration_seconds)
        slo_tracker.record(stage, success)

        if success:
            EVENTS_PROCESSED.labels(stage=stage).inc()
        else:
            EVENTS_FAILED.labels(stage=stage, error_type=error_type).inc()


def record_inflow(stage: str, count: int = 1):
    """call when new events show up at a stage, before processing"""
    with _lock:
        tracker.record_inflow(stage, count)


def set_queue_depth(stage: str, depth: int):
    with _lock:
        _queue_depths[stage] = depth
        QUEUE_DEPTH.labels(stage=stage).set(depth)


def set_processing_lag(stage: str, lag_seconds: float):
    PROCESSING_LAG.labels(stage=stage).set(lag_seconds)
    with _lock:
        anomaly_detector.observe(stage, lag_seconds)


def _derived_metrics_loop(interval: float = 5.0):
    while True:
        start = time.time()
        with _lock:
            update_derived_metrics(tracker, _queue_depths)
            slo_tracker.update_metrics()
        SCRAPE_DURATION.observe(time.time() - start)
        EXPORTER_UP.set(1)
        time.sleep(interval)


def simulate_pipeline():
    """fake traffic generator, delete once hooked up to the real pipeline"""
    tick = 0
    while True:
        tick += 1
        for stage in STAGES:
            record_inflow(stage, count=random.randint(1, 5))
            depth = max(0, _queue_depths[stage] + random.randint(-2, 4))
            set_queue_depth(stage, depth)

            # occasional lag spike so anomaly detection has something to catch
            base_lag = random.uniform(0, 1.5)
            if tick % 40 == 0 and stage == "transform":
                base_lag += 8  # injected spike
            set_processing_lag(stage, round(base_lag, 3))

            duration = random.uniform(0.01, 0.4)
            success = random.random() > 0.05
            record_event(
                stage,
                duration,
                success=success,
                error_type="timeout" if not success else "none",
            )
        time.sleep(1)


def main(port: int = 8000):
    print(f"serving /metrics on http://localhost:{port}/metrics")
    start_http_server(port)

    threading.Thread(target=_derived_metrics_loop, daemon=True).start()
    threading.Thread(target=simulate_pipeline, daemon=True).start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
