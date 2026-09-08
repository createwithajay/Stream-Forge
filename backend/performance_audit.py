"""
VisionEdge TensorRT Performance Audit

Measures inference throughput and latency.

The audit works in SIMULATED mode on the current
development machine and is ready for REAL_TENSORRT
benchmarking when an NVIDIA GPU environment is available.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from inference_engine import InferenceEngine


@dataclass
class PerformanceResult:
    frames: int
    total_time_seconds: float
    average_fps: float
    average_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    inference_mode: str


class TensorRTPerformanceAudit:
    """Benchmark the VisionEdge inference engine."""

    def __init__(self, frames: int = 100):
        self.frames = frames
        self.engine = InferenceEngine()

    def run(self) -> PerformanceResult:
        """Run the inference benchmark."""

        test_frame = np.zeros(
            (720, 1280, 3),
            dtype=np.uint8,
        )

        latencies = []

        start = time.perf_counter()

        for _ in range(self.frames):

            result = self.engine.infer(test_frame)

            latencies.append(
                result["inference_latency_ms"]
            )

        elapsed = time.perf_counter() - start

        average_fps = (
            self.frames / elapsed
            if elapsed > 0
            else 0
        )

        return PerformanceResult(
            frames=self.frames,
            total_time_seconds=round(elapsed, 4),
            average_fps=round(average_fps, 2),
            average_latency_ms=round(
                sum(latencies) / len(latencies),
                3,
            ),
            min_latency_ms=round(
                min(latencies),
                3,
            ),
            max_latency_ms=round(
                max(latencies),
                3,
            ),
            inference_mode=self.engine.mode,
        )

    def report(self, result: PerformanceResult):
        """Print a structured performance report."""

        print()
        print("VisionEdge TensorRT Performance Audit")
        print("=" * 42)

        print(f"Frames tested:       {result.frames}")
        print(
            f"Total time:          "
            f"{result.total_time_seconds} sec"
        )
        print(
            f"Average FPS:         "
            f"{result.average_fps}"
        )
        print(
            f"Average latency:     "
            f"{result.average_latency_ms} ms"
        )
        print(
            f"Minimum latency:     "
            f"{result.min_latency_ms} ms"
        )
        print(
            f"Maximum latency:     "
            f"{result.max_latency_ms} ms"
        )
        print(
            f"Inference mode:      "
            f"{result.inference_mode}"
        )

        print()

        if result.inference_mode == "REAL_TENSORRT":
            print("TensorRT benchmark: REAL")
        else:
            print(
                "TensorRT benchmark: SIMULATED "
                "(hardware unavailable)"
            )

        print()
        print("Performance audit completed successfully.")


if __name__ == "__main__":

    audit = TensorRTPerformanceAudit(
        frames=100
    )

    result = audit.run()

    audit.report(result)