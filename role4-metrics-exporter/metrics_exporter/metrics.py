from prometheus_client import Counter, Gauge, Histogram

# core throughput / lag
EVENTS_PROCESSED = Counter(
    "events_processed_total",
    "events successfully processed",
    ["stage"],
)

EVENTS_FAILED = Counter(
    "events_failed_total",
    "events that failed",
    ["stage", "error_type"],
)

PROCESSING_LAG = Gauge(
    "processing_lag_seconds",
    "how far behind real-time this stage is",
    ["stage"],
)

QUEUE_DEPTH = Gauge(
    "queue_depth",
    "events waiting to be processed",
    ["stage"],
)

# latency as a histogram so we can pull p95/p99 later instead of just avg
PROCESSING_DURATION = Histogram(
    "processing_duration_seconds",
    "time to process one event",
    ["stage"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

# derived metrics, computed in backpressure.py
BACKPRESSURE_INDEX = Gauge(
    "backpressure_index",
    "(inflow - outflow) / inflow per stage, positive = falling behind",
    ["stage"],
)

TIME_TO_DRAIN = Gauge(
    "time_to_drain_seconds",
    "queue_depth / current outflow rate",
    ["stage"],
)

# anomaly detection - rolling z-score per stage on lag
ANOMALY_SCORE = Gauge(
    "anomaly_score",
    "z-score of current lag vs rolling baseline, per stage",
    ["stage"],
)

ANOMALY_DETECTED = Gauge(
    "anomaly_detected",
    "1 if current lag is a statistical outlier vs rolling baseline",
    ["stage"],
)

# SLO / error budget tracking
SLO_ERROR_BUDGET_REMAINING = Gauge(
    "slo_error_budget_remaining_ratio",
    "fraction of error budget left, per stage, over the tracking window",
    ["stage"],
)

SLO_BURN_RATE = Gauge(
    "slo_burn_rate",
    "how many times faster than sustainable the error budget is being spent",
    ["stage"],
)

# scaling signal
SCALING_RECOMMENDATION = Gauge(
    "scaling_recommendation",
    "-1 scale down, 0 stay, 1 scale up -- derived from backpressure + drain time",
    ["stage"],
)

# exporter self-health
EXPORTER_UP = Gauge("exporter_up", "1 if exporter is alive")

SCRAPE_DURATION = Histogram(
    "scrape_duration_seconds",
    "time to build the /metrics response",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)
