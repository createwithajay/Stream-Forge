"""
StreamForge Throughput Audit (Role 4 - Week 2)

Unlike benchmark.py (which only measures how fast events are *submitted*
into the queue), this script measures the *actual end-to-end processing
throughput* of the worker pool:

1. Reset the system to a clean state.
2. Submit N events in safe chunks (respecting the queue size so nothing
   gets rejected).
3. Poll /api/status until every submitted event has been processed.
4. Compute real sustained events/sec across the whole run.
5. Pull p95 / average latency straight from the Prometheus histogram
   exposed at /metrics.
6. Print an honest report and save it to audit_report.md as evidence
   for the GitHub commit / Mid Review.

Run the app first:
    uvicorn app.main:app --reload

Then in another terminal:
    python throughput_audit.py --events 100000 --workers 4
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import time
from datetime import datetime

import requests

CSV_PATH = "audit_results.csv"
CSV_FIELDS = [
    "timestamp",
    "workers",
    "events_requested",
    "events_accepted",
    "events_rejected",
    "total_elapsed_s",
    "throughput_events_per_sec",
    "avg_latency_ms",
    "p95_latency_bucket_s",
]


def append_csv_row(row: dict) -> None:
    """Append one audit run to audit_results.csv, creating it with a header if needed.

    Keeping every run (not just the latest) lets us plot how throughput scales
    as STREAMFORGE_WORKERS changes across separate server restarts.
    """
    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def reset(url: str) -> None:
    r = requests.post(f"{url}/api/reset", timeout=10)
    r.raise_for_status()


def status(url: str) -> dict:
    r = requests.get(f"{url}/api/status", timeout=10)
    r.raise_for_status()
    return r.json()


def submit_in_chunks(url: str, total_events: int, chunk_size: int) -> tuple[int, int]:
    """Submit events in chunks so we never exceed the queue size in one call."""
    accepted = 0
    rejected = 0
    remaining = total_events
    while remaining > 0:
        this_chunk = min(chunk_size, remaining)
        r = requests.post(f"{url}/api/generate", params={"count": this_chunk}, timeout=120)
        r.raise_for_status()
        result = r.json()
        accepted += result["accepted"]
        rejected += result["rejected"]
        remaining -= this_chunk

        # Give workers a moment to drain if the queue is filling up faster
        # than they can process, so subsequent chunks don't get rejected.
        while status(url)["queue_depth"] > chunk_size * 0.8:
            time.sleep(0.1)

    return accepted, rejected


def wait_for_drain(url: str, expected_processed: int, timeout_s: float = 300) -> float:
    """Poll /api/status until processed count catches up. Returns elapsed seconds."""
    started = time.perf_counter()
    while time.perf_counter() - started < timeout_s:
        s = status(url)
        if s["processed"] >= expected_processed and s["queue_depth"] == 0:
            return time.perf_counter() - started
        time.sleep(0.2)
    raise TimeoutError(
        f"Workers did not finish processing within {timeout_s}s "
        f"(processed={status(url)['processed']}, expected={expected_processed})"
    )


def fetch_latency_percentiles(url: str) -> dict:
    """Parse the Prometheus histogram for streamforge_processing_seconds."""
    r = requests.get(f"{url}/metrics", timeout=10)
    r.raise_for_status()
    text = r.text

    buckets = {}
    for line in text.splitlines():
        m = re.match(r'streamforge_processing_seconds_bucket\{le="([^"]+)"\} (\S+)', line)
        if m:
            le = m.group(1)
            count = float(m.group(2))
            buckets[le] = count

    sum_match = re.search(r"streamforge_processing_seconds_sum (\S+)", text)
    count_match = re.search(r"streamforge_processing_seconds_count (\S+)", text)
    total_sum = float(sum_match.group(1)) if sum_match else 0.0
    total_count = float(count_match.group(1)) if count_match else 0.0

    avg = (total_sum / total_count) if total_count else 0.0

    # Approximate p95 from cumulative histogram buckets.
    p95 = None
    if total_count:
        target = total_count * 0.95
        for le_str, cum_count in sorted(buckets.items(), key=lambda kv: float(kv[0]) if kv[0] != "+Inf" else float("inf")):
            if cum_count >= target:
                p95 = le_str
                break

    return {"avg_latency_s": avg, "p95_latency_bucket_s": p95, "sample_count": total_count}


def main() -> None:
    parser = argparse.ArgumentParser(description="StreamForge processing throughput audit")
    parser.add_argument("--events", type=int, default=100_000, help="Total events to push through the pipeline")
    parser.add_argument("--chunk-size", type=int, default=20_000, help="Events submitted per /api/generate call")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    print(f"[1/5] Resetting StreamForge at {args.url} ...")
    reset(args.url)

    print(f"[2/5] Submitting {args.events:,} events in chunks of {args.chunk_size:,} ...")
    submit_started = time.perf_counter()
    accepted, rejected = submit_in_chunks(args.url, args.events, args.chunk_size)
    submit_elapsed = time.perf_counter() - submit_started
    print(f"      accepted={accepted:,} rejected={rejected:,} (submit phase took {submit_elapsed:.2f}s)")

    print("[3/5] Waiting for workers to finish processing everything already accepted ...")
    process_elapsed = wait_for_drain(args.url, expected_processed=accepted)

    total_elapsed = submit_elapsed + process_elapsed
    throughput = accepted / total_elapsed if total_elapsed else 0.0

    print("[4/5] Reading latency percentiles from /metrics ...")
    latency = fetch_latency_percentiles(args.url)

    final_status = status(args.url)

    print("\n=== StreamForge Throughput Audit ===")
    print(f"Events accepted:         {accepted:,}")
    print(f"Events rejected:         {rejected:,}")
    print(f"Total wall time:         {total_elapsed:.2f}s  (submit {submit_elapsed:.2f}s + drain {process_elapsed:.2f}s)")
    print(f"Sustained throughput:    {throughput:,.2f} events/sec")
    print(f"Avg processing latency:  {latency['avg_latency_s']*1000:.3f} ms")
    print(f"p95 latency (bucket):    {latency['p95_latency_bucket_s']}s")
    print(f"Workers alive at end:    {sum(1 for w in final_status['workers'] if w['alive'])}/{len(final_status['workers'])}")

    print(
        "\nNote: this number reflects actual measured throughput on this machine "
        "with the current STREAMFORGE_WORKERS / STREAMFORGE_PROCESSING_DELAY_MS settings. "
        "Do not present it as a universal '100,000 events/sec' claim unless this run actually hit that."
    )

    workers_alive = sum(1 for w in final_status["workers"] if w["alive"])
    worker_count = len(final_status["workers"])

    print("\n[5/5] Writing audit_report.md and appending to audit_results.csv ...")
    with open("audit_report.md", "w", encoding="utf-8") as f:
        f.write("# StreamForge Throughput Audit\n\n")
        f.write(f"- Run at: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"- Worker count: {worker_count}\n")
        f.write(f"- Events accepted: {accepted:,}\n")
        f.write(f"- Events rejected: {rejected:,}\n")
        f.write(f"- Total wall time: {total_elapsed:.2f}s\n")
        f.write(f"- Sustained throughput: {throughput:,.2f} events/sec\n")
        f.write(f"- Avg processing latency: {latency['avg_latency_s']*1000:.3f} ms\n")
        f.write(f"- p95 latency (bucket): {latency['p95_latency_bucket_s']}s\n")
        f.write(f"- Workers alive at end: {workers_alive}/{worker_count}\n")

    append_csv_row(
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "workers": worker_count,
            "events_requested": args.events,
            "events_accepted": accepted,
            "events_rejected": rejected,
            "total_elapsed_s": round(total_elapsed, 3),
            "throughput_events_per_sec": round(throughput, 2),
            "avg_latency_ms": round(latency["avg_latency_s"] * 1000, 4),
            "p95_latency_bucket_s": latency["p95_latency_bucket_s"],
        }
    )
    print(f"      done -> audit_report.md, {CSV_PATH}")
    print(
        "\nTip: restart the app with a different STREAMFORGE_WORKERS value "
        "(1, 2, 4, 8 ...) and re-run this script each time. Every run appends "
        "a new row to audit_results.csv, which plot_audit_results.py turns "
        "into a throughput-vs-workers chart."
    )


if __name__ == "__main__":
    main()
