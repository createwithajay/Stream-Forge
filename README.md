# Stream-Forge

StreamForge is a distributed Python event processing and reliability engineering project.

This repository contains the core StreamForge Reliability Lab together with the VisionEdge hardware-aware video monitoring work contributed by Role 5.

---

# StreamForge Reliability Lab

A local-first reliability and chaos engineering playground for high-throughput Python event processing.

## Features

### Reliability
- Supervisor-managed worker processes
- Automatic worker restart
- Queue-depth monitoring
- Event success/error tracking
- Worker health and restart counters

### Performance
- Configurable event generator
- Throughput benchmark
- Average and p95 processing latency
- Events-per-second measurement
- Backpressure visibility

### Chaos Engineering
- Stop a selected worker
- Simulate worker failure
- Observe queue growth and recovery
- Compare before/after throughput
- Recovery-time measurement

### Observability
- `/metrics` Prometheus endpoint
- JSON health/status endpoints
- Live browser dashboard
- Structured application logs

## Architecture

```text
Event Generator
       |
       v
 Shared Queue
       |
       +--------+--------+--------+
       |        |        |        |
    Worker1 Worker2    ...     WorkerN
       |        |                 |
       +--------+-----------------+
                |
                v
        Metrics Registry
                |
                v
        FastAPI Dashboards