"""
VisionEdge Video Decoder

PyAV-based video/RTSP decoding layer.

Supports:
- Local video files
- RTSP streams
- Mock frame generation
- CPU fallback when hardware decoding is unavailable
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional

import av
import numpy as np


@dataclass
class DecodedFrame:
    """Represents one decoded video frame."""

    frame_id: int
    timestamp: float
    width: int
    height: int
    fps: float
    source: str
    image: np.ndarray


class VideoDecoder:
    """
    PyAV video decoder.

    The decoder can open:
    - MP4/video files
    - RTSP URLs
    - other FFmpeg-compatible sources
    """

    def __init__(
        self,
        source: str,
        stream_index: int = 0,
        max_frames: Optional[int] = None,
    ):
        self.source = source
        self.stream_index = stream_index
        self.max_frames = max_frames

        self.container = None
        self.stream = None

        self.frames_decoded = 0
        self.started_at = None
        self.last_frame_time = None

    def open(self) -> None:
        """Open the video source using PyAV."""

        self.container = av.open(self.source)

        video_streams = [
            stream
            for stream in self.container.streams
            if stream.type == "video"
        ]

        if not video_streams:
            raise RuntimeError(
                f"No video stream found in source: {self.source}"
            )

        if self.stream_index >= len(video_streams):
            raise IndexError(
                f"Video stream index {self.stream_index} "
                f"is unavailable."
            )

        self.stream = video_streams[self.stream_index]

        # Reduce buffering for live sources where supported.
        self.stream.thread_type = "AUTO"

        self.started_at = time.perf_counter()

    def frames(self) -> Generator[DecodedFrame, None, None]:
        """
        Decode frames from the opened source.

        Frames are converted to NumPy BGR24 arrays.
        """

        if self.container is None or self.stream is None:
            self.open()

        for frame in self.container.decode(self.stream):

            if (
                self.max_frames is not None
                and self.frames_decoded >= self.max_frames
            ):
                break

            image = frame.to_ndarray(format="bgr24")

            self.frames_decoded += 1
            self.last_frame_time = time.perf_counter()

            fps = 0.0

            if self.stream.average_rate:
                try:
                    fps = float(self.stream.average_rate)
                except (TypeError, ValueError):
                    fps = 0.0

            yield DecodedFrame(
                frame_id=self.frames_decoded,
                timestamp=float(frame.time or 0.0),
                width=frame.width,
                height=frame.height,
                fps=fps,
                source=self.source,
                image=image,
            )

    def close(self) -> None:
        """Close the video container."""

        if self.container is not None:
            self.container.close()
            self.container = None
            self.stream = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class MockVideoDecoder:
    """
    Generates synthetic frames for development/testing.

    This allows the VisionEdge pipeline to be tested without
    an RTSP camera or NVIDIA hardware.
    """

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        fps: float = 30.0,
        max_frames: int = 300,
        source: str = "mock://camera",
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.max_frames = max_frames
        self.source = source

        self.frames_decoded = 0

    def frames(self) -> Generator[DecodedFrame, None, None]:
        """Generate synthetic video frames."""

        frame_interval = 1.0 / self.fps

        for frame_id in range(1, self.max_frames + 1):

            start = time.perf_counter()

            image = np.zeros(
                (self.height, self.width, 3),
                dtype=np.uint8,
            )

            # Moving rectangle representing a tracked object.
            box_width = 180
            box_height = 120

            max_x = max(self.width - box_width, 1)
            max_y = max(self.height - box_height, 1)

            x = (frame_id * 8) % max_x
            y = (frame_id * 5) % max_y

            image[
                y : y + box_height,
                x : x + box_width,
            ] = (0, 255, 0)

            self.frames_decoded += 1

            yield DecodedFrame(
                frame_id=frame_id,
                timestamp=frame_id / self.fps,
                width=self.width,
                height=self.height,
                fps=self.fps,
                source=self.source,
                image=image,
            )

            elapsed = time.perf_counter() - start

            remaining = frame_interval - elapsed

            if remaining > 0:
                time.sleep(remaining)


def create_decoder(
    source: str,
    max_frames: Optional[int] = None,
):
    """
    Create the appropriate decoder.

    mock:// sources use MockVideoDecoder.
    Everything else uses PyAV.
    """

    if source.startswith("mock://"):
        return MockVideoDecoder(
            max_frames=max_frames or 300,
            source=source,
        )

    return VideoDecoder(
        source=source,
        max_frames=max_frames,
    )


def decoder_status() -> dict:
    """Return decoder capability information."""

    return {
        "decoder": "PyAV",
        "pyav_version": av.__version__,
        "available": True,
        "hardware_acceleration": False,
        "mode": "CPU_DECODE",
        "supported_sources": [
            "RTSP",
            "MP4",
            "AVI",
            "MKV",
            "FFmpeg-compatible sources",
            "mock://",
        ],
        "note": (
            "NVIDIA hardware decoding is not available on the "
            "current development machine."
        ),
    }


if __name__ == "__main__":
    print("VisionEdge Video Decoder")
    print("=" * 30)

    status = decoder_status()

    for key, value in status.items():
        print(f"{key}: {value}")

    print()
    print("Testing mock decoder...")

    decoder = create_decoder(
        "mock://camera",
        max_frames=5,
    )

    for frame in decoder.frames():
        print(
            f"Frame {frame.frame_id}: "
            f"{frame.width}x{frame.height}, "
            f"FPS={frame.fps}, "
            f"shape={frame.image.shape}"
        )

    print()
    print("Mock decoder test completed successfully.")

def validate_rtsp_source(source: str) -> dict:
    """
    Validate an RTSP source without starting a long-running
    decoding loop.
    """

    if not source:
        return {
            "valid": False,
            "source": source,
            "protocol": None,
            "reachable": False,
            "message": "RTSP source is empty.",
        }

    if not source.lower().startswith("rtsp://"):
        return {
            "valid": False,
            "source": source,
            "protocol": "NON_RTSP",
            "reachable": False,
            "message": "Source must start with rtsp://",
        }

    try:
        import av

        container = av.open(
            source,
            mode="r",
            timeout=5.0,
        )

        video_streams = [
            stream
            for stream in container.streams
            if stream.type == "video"
        ]

        container.close()

        if not video_streams:
            return {
                "valid": True,
                "source": source,
                "protocol": "RTSP",
                "reachable": True,
                "video_stream": False,
                "message": "RTSP source opened, but no video stream was found.",
            }

        stream = video_streams[0]

        return {
            "valid": True,
            "source": source,
            "protocol": "RTSP",
            "reachable": True,
            "video_stream": True,
            "width": stream.codec_context.width,
            "height": stream.codec_context.height,
            "codec": stream.codec_context.name,
            "message": "RTSP source opened successfully.",
        }

    except Exception as exc:
        return {
            "valid": True,
            "source": source,
            "protocol": "RTSP",
            "reachable": False,
            "video_stream": False,
            "message": f"Unable to open RTSP source: {exc}",
        }