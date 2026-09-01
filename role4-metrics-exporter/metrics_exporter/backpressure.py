"""
backpressure index + time-to-drain calc.

backpressure = (inflow_rate - outflow_rate) / inflow_rate
  0ish = keeping up, near 1 = basically stuck, negative = draining fine

time_to_drain = queue_depth / outflow_rate
  rough eta in seconds for the backlog to clear at current speed
"""

import time
from collections import defaultdict

from .metrics import BACKPRESSURE_INDEX, SCALING_RECOMMENDATION, TIME_TO_DRAIN


class RateTracker:
    """tracks inflow/outflow per stage over a rolling window, no external tsdb needed"""

    def __init__(self, window_seconds: float = 10.0):
        self.window_seconds = window_seconds
        self._inflow = defaultdict(list)
        self._outflow = defaultdict(list)

    def record_inflow(self, stage: str, count: int = 1):
        self._inflow[stage].append((time.time(), count))
        self._trim(self._inflow[stage])

    def record_outflow(self, stage: str, count: int = 1):
        self._outflow[stage].append((time.time(), count))
        self._trim(self._outflow[stage])

    def _trim(self, events):
        cutoff = time.time() - self.window_seconds
        while events and events[0][0] < cutoff:
            events.pop(0)

    def rate(self, events) -> float:
        self._trim(events)
        if not events:
            return 0.0
        total = sum(c for _, c in events)
        return total / self.window_seconds

    def inflow_rate(self, stage: str) -> float:
        return self.rate(self._inflow[stage])

    def outflow_rate(self, stage: str) -> float:
        return self.rate(self._outflow[stage])

    def all_stages(self):
        return set(self._inflow.keys()) | set(self._outflow.keys())


def update_derived_metrics(tracker: RateTracker, queue_depths: dict):
    for stage in tracker.all_stages():
        inflow = tracker.inflow_rate(stage)
        outflow = tracker.outflow_rate(stage)

        bp = (inflow - outflow) / inflow if inflow > 0 else 0.0
        BACKPRESSURE_INDEX.labels(stage=stage).set(bp)

        depth = queue_depths.get(stage, 0)
        if outflow > 0:
            drain = depth / outflow
        else:
            drain = float("inf") if depth > 0 else 0.0
        drain_capped = min(drain, 999999)
        TIME_TO_DRAIN.labels(stage=stage).set(drain_capped)

        # scaling signal: backed up AND slow to drain -> scale up.
        # basically idle AND draining instantly -> scale down candidate.
        if bp > 0.3 and drain_capped > 15:
            rec = 1
        elif bp < -0.2 and depth < 2:
            rec = -1
        else:
            rec = 0
        SCALING_RECOMMENDATION.labels(stage=stage).set(rec)
