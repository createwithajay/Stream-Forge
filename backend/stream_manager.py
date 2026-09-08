import asyncio
from dataclasses import dataclass
from typing import Dict


@dataclass
class StreamState:
    stream_id: int
    name: str
    status: str = "STOPPED"
    fps: float = 0.0
    frames_processed: int = 0
    detections: int = 0
    processing_mode: str = "SIMULATED"


class StreamManager:
    """
    Multi-stream orchestration manager for VisionEdge.

    The current development environment uses simulated frame
    processing. The architecture is designed so real video
    decoding and TensorRT inference can be connected later.
    """

    TARGET_FPS = 30

    def __init__(self):
        self.streams: Dict[int, StreamState] = {}
        self.tasks: Dict[int, asyncio.Task] = {}

    def add_stream(self, stream_id: int, name: str):
        """Register a new video stream."""

        if stream_id not in self.streams:
            self.streams[stream_id] = StreamState(
                stream_id=stream_id,
                name=name,
            )

    async def _process_stream(self, stream_id: int):
        """Run the asynchronous processing loop for one stream."""

        stream = self.streams[stream_id]
        stream.status = "RUNNING"

        loop = asyncio.get_running_loop()

        while True:
            frame_start = loop.time()

            # Simulated frame processing.
            # Real decoder + TensorRT inference can be connected here.
            await asyncio.sleep(1 / self.TARGET_FPS)

            stream.frames_processed += 1

            # Simulated inference result.
            stream.detections += 1

            elapsed = loop.time() - frame_start

            if elapsed > 0:
                stream.fps = round(1 / elapsed, 2)

    async def start_stream(self, stream_id: int):
        """Start processing a registered stream."""

        if stream_id not in self.streams:
            raise ValueError(
                f"Stream {stream_id} does not exist"
            )

        if stream_id in self.tasks:
            return

        task = asyncio.create_task(
            self._process_stream(stream_id)
        )

        self.tasks[stream_id] = task

    async def stop_stream(self, stream_id: int):
        """Stop processing a stream safely."""

        task = self.tasks.get(stream_id)

        if task:
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            del self.tasks[stream_id]

        if stream_id in self.streams:
            self.streams[stream_id].status = "STOPPED"

    async def start_all(self):
        """Start all registered streams."""

        for stream_id in self.streams:
            await self.start_stream(stream_id)

    async def stop_all(self):
        """Stop all running streams."""

        for stream_id in list(self.tasks.keys()):
            await self.stop_stream(stream_id)

    def get_streams(self):
        """Return telemetry for every registered stream."""

        return [
            {
                "stream_id": stream.stream_id,
                "name": stream.name,
                "status": stream.status,
                "fps": stream.fps,
                "frames_processed": stream.frames_processed,
                "detections": stream.detections,
                "processing_mode": stream.processing_mode,
            }
            for stream in self.streams.values()
        ]


# Global VisionEdge stream manager
stream_manager = StreamManager()


# Register VisionEdge camera streams
stream_manager.add_stream(1, "Camera 01")
stream_manager.add_stream(2, "Camera 02")
stream_manager.add_stream(3, "Camera 03")
stream_manager.add_stream(4, "Camera 04")