\# StreamForge Throughput Audit — Week 2 (Role 4)



\## Method

Built `throughput\_audit.py` to submit a sustained load of real events against

the running StreamForge app and measure actual end-to-end throughput (not just

submission rate). Tested across worker counts of 1, 2, 4, and 8 to see how

throughput scales with parallelism.



\## Results



| Workers | Throughput (events/sec) | Avg Latency (ms) |

|---|---|---|

| 1 | 1,150.62 | 0.589 |

| 2 | 2,152.85 | 0.547 |

| 4 | 3,618.95 | 0.557 |

| 8 | 3,761.30 | 0.710 |



Latest full-scale run (500,000 events):

\- 4 workers: 4,995–5,182 events/sec sustained

\- 8 workers: 3,218.40 events/sec sustained, avg latency 0.909 ms



See `audit\_scaling\_chart.png` for the visual scaling curve.



\## Key finding

Throughput scales near-linearly from 1 to 4 workers. From 4 to 8 workers,

throughput plateaus and, under sustained 500k-event load, actually \*\*drops\*\*

alongside rising latency — despite the test machine having 12 CPU cores

available. Since core count isn't the limiting factor, the bottleneck is most

likely contention in the shared multiprocessing queue (lock contention and/or

per-event serialization overhead), not raw CPU capacity.



\## Path to 100,000 events/sec

We do not claim to have hit 100,000 events/sec — this reflects real, measured

throughput on local hardware with the current single-shared-queue architecture.

To scale further:

1\. Replace the single shared `multiprocessing.Queue` with partitioned queues

&#x20;  per worker, removing the lock-contention bottleneck.

2\. Move to Kafka as the primary queue/broker (already planned per the project

&#x20;  spec), which is designed for exactly this kind of high-throughput,

&#x20;  multi-consumer workload.

3\. Scale horizontally across multiple machines/containers rather than adding

&#x20;  more worker processes on a single box.



\## Files

\- `throughput\_audit.py` — load generator + measurement tool

\- `benchmark.py` — quick local benchmark utility

\- `audit\_results.csv` — raw results across all runs

\- `audit\_scaling\_chart.png` — throughput vs. worker count chart

