"""
example of wiring this into the real pipeline. copy the pattern into your
actual pipeline code, then delete this file / stop calling simulate_pipeline().
"""

import time

from metrics_exporter.exporter import (
    main,
    record_event,
    record_inflow,
    set_processing_lag,
    set_queue_depth,
)


def handle_event(stage: str, event):
    record_inflow(stage)

    start = time.time()
    try:
        # your real processing goes here
        # result = do_transform(event)
        success = True
        error_type = "none"
    except Exception:
        success = False
        error_type = "exception"
    duration = time.time() - start

    record_event(stage, duration, success=success, error_type=error_type)


def update_queue_state(stage: str, current_depth: int, lag_seconds: float):
    set_queue_depth(stage, current_depth)
    set_processing_lag(stage, lag_seconds)


if __name__ == "__main__":
    main(port=8000)
