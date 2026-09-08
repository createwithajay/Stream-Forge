"""
VisionEdge Frame Drawing Layer

Hardware-aware drawing utilities for detection overlays.

CPU_FALLBACK:
    Uses OpenCV + NumPy.

REAL_CUDA:
    Uses the VisionEdge memory layer and can be extended for
    CUDA-native drawing on NVIDIA deployment hardware.
"""

from typing import Any, Iterable

import cv2
import numpy as np

from gpu_memory import GPUMemoryManager, gpu_memory_manager


class FrameDrawer:
    """Draw detection overlays using the VisionEdge memory layer."""

    def __init__(self, memory_manager: GPUMemoryManager | None = None):
        self.memory = memory_manager or gpu_memory_manager

    @staticmethod
    def _get_value(detection: Any, name: str, default=None):
        """Read a detection field from either a dict or an object."""

        if isinstance(detection, dict):
            return detection.get(name, default)

        return getattr(detection, name, default)

    def draw_detection(
        self,
        frame: Any,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        label: str = "object",
        confidence: float = 0.0,
    ) -> Any:
        """Draw one detection box and label."""

        cpu_frame = self.memory.download(frame)

        cv2.rectangle(
            cpu_frame,
            (int(x1), int(y1)),
            (int(x2), int(y2)),
            (0, 255, 0),
            2,
        )

        text = f"{label} {float(confidence):.2f}"

        cv2.putText(
            cpu_frame,
            text,
            (int(x1), max(20, int(y1) - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        if self.memory.mode == "REAL_CUDA":
            return self.memory.upload(cpu_frame)

        return cpu_frame

    def draw_detections(
        self,
        frame: Any,
        detections: Iterable[Any],
    ) -> Any:
        """Draw multiple detection results."""

        result = frame

        for detection in detections:

            x1 = self._get_value(detection, "x1", 0)
            y1 = self._get_value(detection, "y1", 0)
            x2 = self._get_value(detection, "x2", 0)
            y2 = self._get_value(detection, "y2", 0)

            label = self._get_value(
                detection,
                "class_name",
                "object",
            )

            confidence = self._get_value(
                detection,
                "confidence",
                0.0,
            )

            result = self.draw_detection(
                result,
                x1,
                y1,
                x2,
                y2,
                label,
                confidence,
            )

        return result

    def status(self) -> dict:
        """Return drawing-layer hardware status."""

        return {
            "component": "VisionEdge Frame Drawer",
            "mode": self.memory.mode,
            "backend": (
                "CuPy + OpenCV"
                if self.memory.mode == "REAL_CUDA"
                else "NumPy + OpenCV"
            ),
            "opencv_available": True,
            "note": (
                "CUDA-aware memory path available."
                if self.memory.mode == "REAL_CUDA"
                else "Drawing is running through CPU fallback."
            ),
        }


frame_drawer = FrameDrawer()


if __name__ == "__main__":

    print("VisionEdge Frame Drawer Test")
    print("-" * 30)

    test_frame = np.zeros(
        (720, 1280, 3),
        dtype=np.uint8,
    )

    test_detection = {
        "x1": 200,
        "y1": 150,
        "x2": 600,
        "y2": 450,
        "class_name": "person",
        "confidence": 0.92,
    }

    result = frame_drawer.draw_detections(
        test_frame,
        [test_detection],
    )

    print(f"Input shape:  {test_frame.shape}")
    print(f"Output shape: {result.shape}")
    print(f"Memory mode:  {frame_drawer.memory.mode}")
    print(f"Backend:      {frame_drawer.status()['backend']}")
    print("Detection overlay test completed successfully.")