"""
rolling z-score anomaly detection on processing lag, per stage.

keeps a small rolling window of recent lag readings per stage, computes
mean + stddev, and scores the newest reading against that baseline.
no ML model, no external service -- just stats, but it's the same idea
behind most "smart alerting" features in tools like Datadog/Grafana.

score > ~2.5 std devs from baseline = flagged as an anomaly.
"""

import statistics
from collections import defaultdict, deque

from .metrics import ANOMALY_DETECTED, ANOMALY_SCORE

ANOMALY_THRESHOLD = 2.5  # std devs
WINDOW_SIZE = 30  # readings kept per stage


class AnomalyDetector:
    def __init__(self, window_size: int = WINDOW_SIZE, threshold: float = ANOMALY_THRESHOLD):
        self.window_size = window_size
        self.threshold = threshold
        self._history = defaultdict(lambda: deque(maxlen=window_size))

    def observe(self, stage: str, value: float):
        history = self._history[stage]

        # not enough data yet to have a meaningful baseline
        if len(history) < 5:
            history.append(value)
            ANOMALY_SCORE.labels(stage=stage).set(0.0)
            ANOMALY_DETECTED.labels(stage=stage).set(0)
            return

        mean = statistics.mean(history)
        stdev = statistics.pstdev(history) or 0.0001  # avoid div by zero on flat data

        z = (value - mean) / stdev
        ANOMALY_SCORE.labels(stage=stage).set(z)
        ANOMALY_DETECTED.labels(stage=stage).set(1 if abs(z) > self.threshold else 0)

        history.append(value)
