import argparse
import time
import uuid
import random
import requests


def main():
    parser = argparse.ArgumentParser(description="StreamForge local throughput benchmark")
    parser.add_argument("--events", type=int, default=50000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    print(f"Submitting {args.events:,} events to {args.url}")
    started = time.perf_counter()

    response = requests.post(
        f"{args.url}/api/generate",
        params={"count": args.events},
        timeout=120,
    )
    response.raise_for_status()
    result = response.json()

    elapsed = time.perf_counter() - started
    print("\n=== StreamForge Benchmark ===")
    print(f"Requested:       {result['requested']:,}")
    print(f"Accepted:        {result['accepted']:,}")
    print(f"Rejected:        {result['rejected']:,}")
    print(f"Submit rate:     {result['submission_rate']:,.2f} events/sec")
    print(f"Client elapsed:  {elapsed:.3f} sec")
    print("\nNote: this is a local benchmark. Do not present 100k events/sec as a guaranteed result unless your hardware actually measures it.")


if __name__ == "__main__":
    main()
