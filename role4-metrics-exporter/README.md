# Metrics Exporter (Role 4)

Prometheus exporter for the pipeline. Covers the basics (lag, throughput,
per-stage latency) plus a few things that go beyond a standard exporter:
backpressure prediction, anomaly detection, SLO burn-rate tracking, and a
scaling recommendation signal. All labeled per stage so Role 5 can bind
each React Flow node straight to its own metrics.

## Run it

```bash
pip install -r requirements.txt
python -m metrics_exporter.exporter
```

Serves `/metrics` on `http://localhost:8000/metrics`. Ships with a fake
traffic generator (including an occasional injected lag spike on the
`transform` stage) so there's real data to look at immediately, and so
the anomaly detector has something to catch. Swap it out for the real
pipeline when ready — see `pipeline_hook_example.py`.

## Hooking into the real pipeline

```python
from metrics_exporter.exporter import record_event, record_inflow, set_queue_depth, set_processing_lag

record_inflow("transform")
record_event("transform", duration_s, success=True)
set_queue_depth("transform", 42)
set_processing_lag("transform", 1.2)
```

Then remove the `simulate_pipeline()` thread call in `exporter.py`.

## Testing with Prometheus locally

```bash
prometheus --config.file=prometheus.yml
```

Queries to try at http://localhost:9090:

- `rate(events_processed_total[1m])` — events/sec per stage
- `rate(events_failed_total[1m])` — failure rate
- `histogram_quantile(0.95, rate(processing_duration_seconds_bucket[5m]))` — p95 latency
- `processing_lag_seconds` — current lag per stage
- `backpressure_index` — is a stage falling behind
- `time_to_drain_seconds` — eta to clear the backlog
- `anomaly_score` / `anomaly_detected` — is current lag statistically unusual
- `slo_burn_rate` / `slo_error_budget_remaining_ratio` — how fast the error budget is being spent
- `scaling_recommendation` — -1/0/1 signal for whether a stage needs more/fewer workers
- `exporter_up` — exporter health

## Metrics reference

| Metric | Type | Labels | What it's for |
|---|---|---|---|
| `events_processed_total` | Counter | stage | throughput |
| `events_failed_total` | Counter | stage, error_type | failure tracking |
| `processing_lag_seconds` | Gauge | stage | current lag |
| `queue_depth` | Gauge | stage | backlog size |
| `processing_duration_seconds` | Histogram | stage | p50/p95/p99 latency |
| `backpressure_index` | Gauge | stage | (inflow−outflow)/inflow, is a stage falling behind |
| `time_to_drain_seconds` | Gauge | stage | eta to clear the backlog |
| `anomaly_score` | Gauge | stage | z-score of lag vs rolling baseline |
| `anomaly_detected` | Gauge | stage | 1 if lag is a statistical outlier |
| `slo_error_budget_remaining_ratio` | Gauge | stage | fraction of error budget left |
| `slo_burn_rate` | Gauge | stage | how many x faster than sustainable the budget is being spent |
| `scaling_recommendation` | Gauge | stage | -1/0/1, scale down/stay/scale up |
| `exporter_up` | Gauge | — | exporter health |
| `scrape_duration_seconds` | Histogram | — | exporter self-health |

## Why these extra metrics

- **Anomaly detection** — rolling z-score per stage instead of a fixed
  threshold. Same core idea behind "smart alerting" in tools like Datadog
  and Grafana, just implemented directly rather than pulled from a paid
  service. Catches lag spikes even when there's no hardcoded rule for
  what "too slow" means.
- **SLO burn rate** — based on the Google SRE error-budget model. A burn
  rate of 1.0 means you're on pace to use exactly 100% of your allowed
  failure budget by the end of the window; 10x means you'll blow through
  it in a tenth of the time. This is the number that should actually
  trigger an alert, not the raw error count.
- **Scaling recommendation** — combines backpressure and drain time into
  a single -1/0/1 signal, so the dashboard (or an autoscaler down the
  line) doesn't have to reason about two numbers separately.
- **Backpressure index / time-to-drain** — predictive rather than
  descriptive. Goes positive before the queue visibly backs up, so a
  dashboard node can turn amber before it's actually stuck.
- **Per-stage labeling throughout** — lets Role 5 bind one PromQL filter
  per React Flow node, e.g. `processing_lag_seconds{stage="transform"}`.

## Handoff notes for Role 5

Query Prometheus's HTTP API directly:

```
GET http://<host>:9090/api/v1/query?query=processing_lag_seconds
```

Match the `stage` label in the response to the corresponding React Flow
node ID. For a quick "health color" per node, `scaling_recommendation`
or `anomaly_detected` are good single-number signals to drive node color
without the frontend needing its own threshold logic.

## Files

```
metrics_exporter/
├── __init__.py
├── metrics.py         # metric definitions
├── backpressure.py    # backpressure index, time-to-drain, scaling signal
├── anomaly.py          # rolling z-score anomaly detection
├── slo.py              # SLO error budget + burn rate
└── exporter.py          # http server + simulator
pipeline_hook_example.py
prometheus.yml
requirements.txt
```
