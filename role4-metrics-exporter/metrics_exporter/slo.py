"""
SLO / error budget tracking, per stage.

pick a target success rate (SLO_TARGET, e.g. 99.5%). over a rolling
window we track how much of the "allowed failure budget" has been used.

burn rate = how many times faster than sustainable you're using up the
budget right now. burn rate of 1.0 = exactly on pace to use 100% of the
budget by the end of the window. burn rate of 10 = you'll blow through
the whole budget in 1/10th of the window -- that's the number that
should actually trigger a page.

this is the same core idea Google SRE popularized (error budgets +
multi-window burn rate alerts), just simplified to one window here.
"""

import time
from collections import defaultdict, deque

from .metrics import SLO_BURN_RATE, SLO_ERROR_BUDGET_REMAINING

SLO_TARGET = 0.995  # 99.5% success target
WINDOW_SECONDS = 300  # 5 minute rolling window


class SLOTracker:
    def __init__(self, target: float = SLO_TARGET, window_seconds: float = WINDOW_SECONDS):
        self.target = target
        self.window_seconds = window_seconds
        self.allowed_failure_rate = 1 - target
        self._events = defaultdict(deque)  # stage -> deque[(ts, success_bool)]

    def record(self, stage: str, success: bool):
        events = self._events[stage]
        events.append((time.time(), success))
        self._trim(events)

    def _trim(self, events):
        cutoff = time.time() - self.window_seconds
        while events and events[0][0] < cutoff:
            events.popleft()

    def update_metrics(self):
        for stage, events in self._events.items():
            self._trim(events)
            if not events:
                continue

            total = len(events)
            failures = sum(1 for _, ok in events if not ok)
            actual_failure_rate = failures / total

            budget_total = self.allowed_failure_rate * total
            budget_used = min(failures, budget_total) if budget_total > 0 else failures
            remaining = 1 - (budget_used / budget_total) if budget_total > 0 else (1.0 if failures == 0 else 0.0)
            remaining = max(0.0, min(1.0, remaining))
            SLO_ERROR_BUDGET_REMAINING.labels(stage=stage).set(remaining)

            burn_rate = (actual_failure_rate / self.allowed_failure_rate) if self.allowed_failure_rate > 0 else 0.0
            SLO_BURN_RATE.labels(stage=stage).set(burn_rate)
