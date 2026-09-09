"""
VisionEdge GPU Memory Layer

Provides a hardware-aware interface for GPU/CPU frame buffers.

REAL_CUDA:
    Used when CuPy and a CUDA-capable NVIDIA GPU are available.

CPU_FALLBACK:
    Used on development machines without CUDA/CuPy.

This module is intentionally hardware-aware so the same pipeline
can run on both development and NVIDIA production machines.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class MemoryStatus:
    mode: str
    cupy_available: bool
    cuda_available: bool
    backend: str
    note: str


class GPUMemoryManager:
    """Manage frame buffers with CUDA-aware fallback."""

    def __init__(self):
        self.cp = None
        self.cupy_available = False
        self.cuda_available = False

        try:
            import cupy as cp

            self.cp = cp
            self.cupy_available = True

            try:
                device_count = cp.cuda.runtime.getDeviceCount()
                self.cuda_available = device_count > 0
            except Exception:
                self.cuda_available = False

        except ImportError:
            self.cp = None

    @property
    def mode(self) -> str:
        if self.cupy_available and self.cuda_available:
            return "REAL_CUDA"

        return "CPU_FALLBACK"

    def status(self) -> dict:
        if self.mode == "REAL_CUDA":
            note = "CuPy CUDA GPU memory is available."
        else:
            note = (
                "CUDA/CuPy GPU memory is unavailable on the current "
                "development machine."
            )

        return {
            "component": "VisionEdge GPU Memory Manager",
            "mode": self.mode,
            "cupy_available": self.cupy_available,
            "cuda_available": self.cuda_available,
            "backend": "CuPy" if self.mode == "REAL_CUDA" else "NumPy",
            "note": note,
        }

    def upload(self, frame: np.ndarray) -> Any:
        """
        Transfer a frame into the active processing memory space.

        On CUDA hardware this creates a CuPy GPU array.
        On fallback systems the original NumPy array is retained.
        """

        if self.mode == "REAL_CUDA":
            return self.cp.asarray(frame)

        return frame

    def download(self, frame: Any) -> np.ndarray:
        """
        Return a NumPy frame for CPU-side consumers.

        CuPy arrays are copied back only when required.
        """

        if self.mode == "REAL_CUDA":
            return self.cp.asnumpy(frame)

        return frame

    def allocate(self, shape, dtype=np.uint8) -> Any:
        """Allocate a processing buffer in the active memory space."""

        if self.mode == "REAL_CUDA":
            return self.cp.zeros(shape, dtype=dtype)

        return np.zeros(shape, dtype=dtype)


gpu_memory_manager = GPUMemoryManager()


if __name__ == "__main__":
    print("VisionEdge GPU Memory Test")
    print("-" * 30)

    status = gpu_memory_manager.status()

    for key, value in status.items():
        print(f"{key}: {value}")

    test_frame = np.zeros(
        (720, 1280, 3),
        dtype=np.uint8,
    )

    buffer = gpu_memory_manager.upload(test_frame)

    print(f"Input shape: {test_frame.shape}")
    print(f"Buffer type: {type(buffer).__name__}")

    restored = gpu_memory_manager.download(buffer)

    print(f"Output shape: {restored.shape}")
    print("GPU memory layer test completed successfully.")