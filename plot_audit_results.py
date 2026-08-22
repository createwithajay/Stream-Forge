"""
StreamForge Audit Visualizer (Role 4 - Week 2)
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict

import matplotlib.pyplot as plt


def load_rows(csv_path: str) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot StreamForge audit scaling results")
    parser.add_argument("--csv", default="audit_results.csv")
    parser.add_argument("--out", default="audit_scaling_chart.png")
    args = parser.parse_args()

    rows = load_rows(args.csv)
    if not rows:
        raise SystemExit(f"No rows found in {args.csv}. Run throughput_audit.py first.")

    by_workers: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_workers[int(row["workers"])].append(row)

    worker_counts = sorted(by_workers.keys())
    avg_throughput = [
        sum(float(r["throughput_events_per_sec"]) for r in by_workers[w]) / len(by_workers[w])
        for w in worker_counts
    ]
    avg_latency_ms = [
        sum(float(r["avg_latency_ms"]) for r in by_workers[w]) / len(by_workers[w])
        for w in worker_counts
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("StreamForge Reliability Lab - Throughput Audit (Role 4)", fontsize=12, fontweight="bold")

    ax1.plot(worker_counts, avg_throughput, marker="o", linewidth=2, color="#2563eb")
    ax1.set_xlabel("Worker count")
    ax1.set_ylabel("Sustained throughput (events/sec)")
    ax1.set_title("Throughput vs Worker Count")
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(worker_counts)

    ax2.bar([str(w) for w in worker_counts], avg_latency_ms, color="#f97316")
    ax2.set_xlabel("Worker count")
    ax2.set_ylabel("Avg processing latency (ms)")
    ax2.set_title("Latency vs Worker Count")
    ax2.grid(True, axis="y", alpha=0.3)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(args.out, dpi=150)
    print(f"Saved chart -> {args.out}")
    print("\nSummary used for the chart:")
    for w, t, l in zip(worker_counts, avg_throughput, avg_latency_ms):
        print(f"  workers={w:<3} throughput={t:,.2f} ev/s   avg_latency={l:.3f} ms")


if __name__ == "__main__":
    main()
