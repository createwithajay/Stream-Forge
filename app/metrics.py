from prometheus_client import Counter, Gauge, Histogram


EVENTS_TOTAL = Counter(
    "streamforge_events_total",
    "Total events processed successfully",
)

EVENTS_FAILED = Counter(
    "streamforge_events_failed_total",
    "Total events that failed processing",
)

PROCESSING_SECONDS = Histogram(
    "streamforge_processing_seconds",
    "Event processing latency in seconds",
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
)

QUEUE_DEPTH = Gauge(
    "streamforge_queue_depth",
    "Current number of events waiting in the queue",
)

WORKER_UP = Gauge(
    "streamforge_worker_up",
    "Whether a worker is alive",
    ["worker_id"],
)

WORKER_RESTARTS = Counter(
    "streamforge_worker_restarts_total",
    "Number of worker restarts",
    ["worker_id"],
)

THROUGHPUT = Gauge(
    "streamforge_events_per_second",
    "Rolling events per second estimate",
)

PROCESSING_LAG = Gauge(
    "streamforge_processing_lag_seconds",
    "Time between an event's creation and when it was fully processed",
)

EVENT_LAG_DISTRIBUTION = Histogram(
    "streamforge_event_lag_distribution_seconds",
    "Distribution of end-to-end lag per event",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)