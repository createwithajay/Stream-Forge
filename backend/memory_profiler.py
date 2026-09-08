"""
VisionEdge Memory Profiler

Tracks system/process memory during pipeline execution.

GPU memory is reported when NVIDIA/CUDA tooling is available.
Otherwise the profiler safely falls back to CPU memory metrics.
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass

import psutil


@dataclass
class MemorySnapshot:
    process_mb: float
    system_used_mb: float
    system_percent: float
    gpu_used_mb: float | None = None
    gpu_total_mb: float | None = None


class MemoryProfiler:
    """Hardware-aware memory profiling for VisionEdge."""

    def __init__(self):
        self.process = psutil.Process(os.getpid())

    def _gpu_memory(self):
        """Read NVIDIA GPU memory using nvidia-smi when available."""

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.returncode != 0:
                return None, None

            line = result.stdout.strip().splitlines()[0]
            used, total = line.split(",")

            return float(used.strip()), float(total.strip())

        except Exception:
            return None, None

    def snapshot(self) -> MemorySnapshot:
        """Capture current process, system and GPU memory."""

        process_mb = self.process.memory_info().rss / (1024 * 1024)

        virtual = psutil.virtual_memory()
        system_used_mb = virtual.used / (1024 * 1024)

        gpu_used_mb, gpu_total_mb = self._gpu_memory()

        return MemorySnapshot(
            process_mb=round(process_mb, 2),
            system_used_mb=round(system_used_mb, 2),
            system_percent=round(virtual.percent, 2),
            gpu_used_mb=gpu_used_mb,
            gpu_total_mb=gpu_total_mb,
        )

    def profile(self, duration_seconds: float = 3.0) -> dict:
        """Measure memory before and after a profiling interval."""

        before = self.snapshot()

        time.sleep(duration_seconds)

        after = self.snapshot()

        process_growth = round(
            after.process_mb - before.process_mb,
            2,
        )

        gpu_growth = None

        if (
            before.gpu_used_mb is not None
            and after.gpu_used_mb is not None
        ):
            gpu_growth = round(
                after.gpu_used_mb - before.gpu_used_mb,
                2,
            )

        return {
            "component": "VisionEdge Memory Profiler",
            "process_memory_before_mb": before.process_mb,
            "process_memory_after_mb": after.process_mb,
            "process_memory_growth_mb": process_growth,
            "system_memory_percent": after.system_percent,
            "gpu_memory_before_mb": before.gpu_used_mb,
            "gpu_memory_after_mb": after.gpu_used_mb,
            "gpu_memory_growth_mb": gpu_growth,
            "gpu_available": after.gpu_used_mb is not None,
            "potential_memory_leak": process_growth > 50,
        }


if __name__ == "__main__":
    print("VisionEdge Memory Profiler")
    print("=" * 32)

    profiler = MemoryProfiler()

    print("\nInitial snapshot:")
    print(profiler.snapshot())

    print("\nRunning 3-second memory profile...")

    result = profiler.profile(3)

    print("\nMemory Profile")
    print("--------------")

    for key, value in result.items():
        print(f"{key}: {value}")

    print("\nMemory profiling test completed successfully.")