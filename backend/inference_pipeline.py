"""
VisionEdge Inference Pipeline

Connects:

Video Decoder
     ↓
GPU Memory Manager
     ↓
Inference Engine
     ↓
Detection Results
     ↓
Telemetry
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from video_decoder import create_decoder
from inference_engine import InferenceEngine
from gpu_memory import GPUMemoryManager


@dataclass
class PipelineStats:
    frames_processed: int = 0
    detections: int = 0
    elapsed_seconds: float = 0.0
    average_fps: float = 0.0
    average_latency_ms: float = 0.0


class InferencePipeline:
    """Connect video decoding, memory management and object inference."""

    def __init__(
        self,
        source: str = "mock://camera",
        max_frames: int = 30,
    ):
        self.source = source
        self.max_frames = max_frames

        self.decoder = create_decoder(
            source,
            max_frames=max_frames,
        )

        self.memory = GPUMemoryManager()

        self.inference = InferenceEngine()

        self.stats = PipelineStats()

    def run(self) -> PipelineStats:
        """Process decoded frames through memory and inference."""

        start_time = time.perf_counter()
        total_latency = 0.0
        total_detections = 0

        for decoded_frame in self.decoder.frames():

            # Move frame into the active processing memory space.
            processing_frame = self.memory.upload(
                decoded_frame.image
            )

            # Run inference.
            #
            # On NVIDIA/CUDA hardware this can receive a CuPy
            # GPU buffer when the inference implementation supports it.
            #
            # On the current development machine this remains a
            # NumPy CPU fallback.
            result = self.inference.infer(
                processing_frame
            )

            latency = result["inference_latency_ms"]

            total_latency += latency
            total_detections += result["detection_count"]

            self.stats.frames_processed += 1

        elapsed = time.perf_counter() - start_time

        self.stats.elapsed_seconds = round(
            elapsed,
            3,
        )

        if self.stats.frames_processed and elapsed > 0:
            self.stats.average_fps = round(
                self.stats.frames_processed / elapsed,
                2,
            )

            self.stats.average_latency_ms = round(
                total_latency / self.stats.frames_processed,
                3,
            )

        self.stats.detections = total_detections

        return self.stats

    def status(self) -> dict:
        """Return current pipeline status."""

        return {
            "source": self.source,
            "decoder": "PyAV",
            "memory": self.memory.status(),
            "inference_engine": "VisionEdge Inference Engine",
            "inference_mode": self.inference.mode,
            "frames_processed": self.stats.frames_processed,
            "detections": self.stats.detections,
            "average_fps": self.stats.average_fps,
            "average_latency_ms": self.stats.average_latency_ms,
        }


if __name__ == "__main__":
    print("VisionEdge Inference Pipeline")
    print("=" * 34)

    pipeline = InferencePipeline(
        source="mock://camera",
        max_frames=30,
    )

    stats = pipeline.run()

    print()
    print("Pipeline Results")
    print("----------------")

    print(f"Frames processed: {stats.frames_processed}")
    print(f"Detections:       {stats.detections}")
    print(f"Elapsed time:     {stats.elapsed_seconds} sec")
    print(f"Average FPS:      {stats.average_fps}")
    print(f"Average latency:  {stats.average_latency_ms} ms")
    print(f"Inference mode:   {pipeline.inference.mode}")
    print(f"Memory mode:      {pipeline.memory.mode}")

    print()
    print("Pipeline status:")
    print(pipeline.status())

    print()
    print("Inference pipeline test completed successfully.")