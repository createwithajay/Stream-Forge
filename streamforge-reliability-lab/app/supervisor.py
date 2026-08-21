from __future__ import annotations

import multiprocessing as mp
import os
import queue
import threading
import time
from dataclasses import dataclass

from .metrics import (
    EVENTS_FAILED,
    EVENTS_TOTAL,
    PROCESSING_SECONDS,
    QUEUE_DEPTH,
    THROUGHPUT,
    WORKER_RESTARTS,
    WORKER_UP,
)


def worker_loop(worker_id: int, event_queue: mp.Queue, result_queue: mp.Queue, stop_event: mp.Event, processing_delay_ms: float) -> None:
    while not stop_event.is_set():
        try:
            event = event_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        started = time.perf_counter()
        try:
            # A tiny deterministic workload keeps the benchmark repeatable.
            if processing_delay_ms > 0:
                time.sleep(processing_delay_ms / 1000.0)

            if event.get("temperature", 0) < -20 or event.get("temperature", 0) > 60:
                raise ValueError("sensor value outside accepted operating range")

            result_queue.put(("success", time.perf_counter() - started))
        except Exception:
            result_queue.put(("failure", time.perf_counter() - started))


@dataclass
class WorkerState:
    worker_id: int
    process: mp.Process | None = None
    stop_event: mp.Event | None = None
    restarts: int = 0


class WorkerSupervisor:
    def __init__(self, worker_count: int, queue_size: int, processing_delay_ms: float) -> None:
        self.queue: mp.Queue = mp.Queue(maxsize=queue_size)
        self.result_queue: mp.Queue = mp.Queue()
        self.worker_count = worker_count
        self.processing_delay_ms = processing_delay_ms
        self.workers = {
            i: WorkerState(i) for i in range(1, worker_count + 1)
        }
        self.started_at = time.perf_counter()
        self.total_submitted = 0
        self.total_processed = 0
        self._lock = threading.Lock()
        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._monitor_thread.start()
        self.start_all()

    def start_all(self) -> None:
        for worker_id in self.workers:
            self.start_worker(worker_id)

    def start_worker(self, worker_id: int) -> None:
        state = self.workers[worker_id]
        if state.process and state.process.is_alive():
            return

        state.stop_event = mp.Event()
        process = mp.Process(
            target=worker_loop,
            args=(worker_id, self.queue, self.result_queue, state.stop_event, self.processing_delay_ms),
            name=f"streamforge-worker-{worker_id}",
            daemon=True,
        )
        process.start()
        state.process = process
        WORKER_UP.labels(str(worker_id)).set(1)

    def stop_worker(self, worker_id: int) -> bool:
        state = self.workers.get(worker_id)
        if not state or not state.process:
            return False

        # Controlled chaos: terminate exactly one worker process.
        if state.process.is_alive():
            state.process.terminate()
            state.process.join(timeout=1)
            WORKER_UP.labels(str(worker_id)).set(0)
            return True
        return False

    def submit(self, event: dict) -> bool:
        try:
            self.queue.put_nowait(event)
            with self._lock:
                self.total_submitted += 1
            return True
        except queue.Full:
            return False

    def _drain_results(self) -> None:
        while True:
            try:
                result, latency = self.result_queue.get_nowait()
            except queue.Empty:
                break
            self.total_processed += 1
            if result == "success":
                EVENTS_TOTAL.inc()
            else:
                EVENTS_FAILED.inc()
            PROCESSING_SECONDS.observe(latency)

    def snapshot(self) -> dict:
        self._drain_results()
        workers = []
        for worker_id, state in self.workers.items():
            alive = bool(state.process and state.process.is_alive())
            workers.append(
                {
                    "worker_id": worker_id,
                    "pid": state.process.pid if state.process else None,
                    "alive": alive,
                    "restarts": state.restarts,
                }
            )

        depth = self.queue.qsize()
        QUEUE_DEPTH.set(depth)

        elapsed = max(time.perf_counter() - self.started_at, 0.001)
        throughput = self.total_processed / elapsed
        THROUGHPUT.set(throughput)

        return {
            "queue_depth": depth,
            "workers": workers,
            "submitted": self.total_submitted,
            "processed": self.total_processed,
            "throughput_estimate": round(throughput, 2),
        }

    def shutdown(self) -> None:
        for state in self.workers.values():
            if state.process and state.process.is_alive():
                state.process.terminate()
                state.process.join(timeout=1)

    def _monitor(self) -> None:
        while True:
            time.sleep(0.5)
            self._drain_results()
            for worker_id, state in self.workers.items():
                if state.process is None:
                    continue

                if not state.process.is_alive():
                    WORKER_UP.labels(str(worker_id)).set(0)
                    state.restarts += 1
                    WORKER_RESTARTS.labels(str(worker_id)).inc()
                    self.start_worker(worker_id)
