import time
import requests


BASE = "http://127.0.0.1:8000"


def status():
    return requests.get(f"{BASE}/api/status", timeout=5).json()


def main():
    print("Starting controlled chaos experiment...")
    print("1) Generate background workload.")
    requests.post(f"{BASE}/api/generate", params={"count": 20000}, timeout=60)

    before = status()
    healthy_worker = next(w for w in before["workers"] if w["alive"])
    worker_id = healthy_worker["worker_id"]

    print(f"2) Terminating Worker {worker_id} (PID {healthy_worker['pid']}).")
    started = time.perf_counter()
    response = requests.post(f"{BASE}/api/chaos/kill/{worker_id}", timeout=5)
    response.raise_for_status()

    print("3) Waiting for supervisor recovery...")
    while True:
        current = status()
        worker = next(w for w in current["workers"] if w["worker_id"] == worker_id)
        if worker["alive"] and worker["restarts"] > healthy_worker["restarts"]:
            break
        time.sleep(0.2)

    recovery = time.perf_counter() - started
    print(f"4) Recovery detected in {recovery:.3f} seconds.")
    print("5) Final status:")
    print(status())
    print("\nChaos experiment complete.")


if __name__ == "__main__":
    main()
