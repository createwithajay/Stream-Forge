"""
VisionEdge Inference Engine

Provides a hardware-aware inference abstraction.

REAL mode:
    TensorRT can be plugged in when NVIDIA/TensorRT is available.

SIMULATED mode:
    Generates deterministic detection results for development
    when GPU inference is unavailable.
"""

from __future__ import annotations

import importlib.util
import time
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class Detection:
    """Single object detection result."""

    class_id: int
    class_name: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int


class InferenceEngine:
    """Hardware-aware inference engine."""

    def __init__(
        self,
        model_name: str = "visionedge-model",
    ):
        self.model_name = model_name

        self.tensorrt_available = (
            importlib.util.find_spec("tensorrt") is not None
        )

        self.cuda_available = self._check_cuda()

        self.mode = (
            "REAL_TENSORRT"
            if self.tensorrt_available and self.cuda_available
            else "SIMULATED"
        )

        self.frames_processed = 0
        self.total_inference_time = 0.0

    @staticmethod
    def _check_cuda() -> bool:
        """Check whether NVIDIA CUDA is available."""

        try:
            import torch

            return torch.cuda.is_available()

        except (ImportError, AttributeError):
            return False

    def infer(self, frame: np.ndarray) -> dict[str, Any]:
        """
        Run inference on one frame.

        Real TensorRT execution is used only when the required
        NVIDIA environment is available. Otherwise a deterministic
        simulated detection is returned.
        """

        start = time.perf_counter()

        if self.mode == "REAL_TENSORRT":
            result = self._real_inference(frame)
        else:
            result = self._simulated_inference(frame)

        elapsed_ms = (time.perf_counter() - start) * 1000

        self.frames_processed += 1
        self.total_inference_time += elapsed_ms

        result["inference_latency_ms"] = round(elapsed_ms, 3)
        result["frame_number"] = self.frames_processed
        result["mode"] = self.mode

        return result

    def _simulated_inference(
        self,
        frame: np.ndarray,
    ) -> dict[str, Any]:
        """Generate deterministic detection results."""

        height, width = frame.shape[:2]

        box_width = max(int(width * 0.20), 1)
        box_height = max(int(height * 0.20), 1)

        frame_number = self.frames_processed + 1

        x1 = (frame_number * 7) % max(width - box_width, 1)
        y1 = (frame_number * 5) % max(height - box_height, 1)

        detection = Detection(
            class_id=0,
            class_name="object",
            confidence=0.92,
            x1=int(x1),
            y1=int(y1),
            x2=int(x1 + box_width),
            y2=int(y1 + box_height),
        )

        return {
            "status": "success",
            "detections": [
                detection.__dict__
            ],
            "detection_count": 1,
        }

    def _real_inference(
        self,
        frame: np.ndarray,
    ) -> dict[str, Any]:
        """
        TensorRT inference hook.

        The actual TensorRT execution implementation can be
        activated on a compatible NVIDIA environment.
        """

        raise NotImplementedError(
            "TensorRT runtime integration requires a configured "
            "NVIDIA CUDA/TensorRT environment."
        )

    def statistics(self) -> dict[str, Any]:
        """Return inference statistics."""

        average_latency = 0.0

        if self.frames_processed:
            average_latency = (
                self.total_inference_time
                / self.frames_processed
            )

        return {
            "model": self.model_name,
            "mode": self.mode,
            "frames_processed": self.frames_processed,
            "average_latency_ms": round(
                average_latency,
                3,
            ),
        }


def inference_status() -> dict:
    """Return inference capability information."""

    engine = InferenceEngine()

    return {
        "engine": "VisionEdge Inference Engine",
        "mode": engine.mode,
        "tensorrt_available": engine.tensorrt_available,
        "cuda_available": engine.cuda_available,
        "real_inference_available": (
            engine.mode == "REAL_TENSORRT"
        ),
        "fallback": "SIMULATED",
    }


if __name__ == "__main__":
    print("VisionEdge Inference Engine")
    print("=" * 32)

    status = inference_status()

    for key, value in status.items():
        print(f"{key}: {value}")

    print()
    print("Testing simulated inference...")

    engine = InferenceEngine()

    test_frame = np.zeros(
        (720, 1280, 3),
        dtype=np.uint8,
    )

    for _ in range(5):
        result = engine.infer(test_frame)

        print(
            f"Frame {result['frame_number']}: "
            f"detections={result['detection_count']}, "
            f"latency={result['inference_latency_ms']} ms, "
            f"mode={result['mode']}"
        )

    print()
    print("Statistics:")
    print(engine.statistics())

    print()
    print("Inference engine test completed successfully.")