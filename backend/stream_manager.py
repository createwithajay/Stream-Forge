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


class StreamManager:
    """
    Manages multiple video streams concurrently using asyncio.
    """

    def __init__(self):
        self.streams: Dict[int, StreamState] = {}
        self.tasks: Dict[int, asyncio.Task] = {}

    def add_stream(self, stream_id: int, name: str):
        """Register a new stream."""

        if stream_id not in self.streams:
            self.streams[stream_id] = StreamState(
                stream_id=stream_id,
                name=name,
            )

    async def _process_stream(self, stream_id: int):
        """
        Simulated asynchronous stream-processing loop.

        This represents where actual video decoding and
        TensorRT inference can later be connected.
        """

        stream = self.streams[stream_id]
        stream.status = "RUNNING"

        while True:
            frame_start = asyncio.get_running_loop().time()

            # Simulate asynchronous frame processing
            await asyncio.sleep(1 / 30)

            stream.frames_processed += 1

            frame_end = asyncio.get_running_loop().time()
            elapsed = frame_end - frame_start

            if elapsed > 0:
                stream.fps = round(1 / elapsed, 2)

    async def start_stream(self, stream_id: int):
        """Start processing a stream."""

        if stream_id not in self.streams:
            raise ValueError(f"Stream {stream_id} does not exist")

        if stream_id in self.tasks:
            return

        task = asyncio.create_task(
            self._process_stream(stream_id)
        )

        self.tasks[stream_id] = task

    async def stop_stream(self, stream_id: int):
        """Stop processing a stream."""

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

    def get_streams(self):
        """Return current stream telemetry."""

        return [
            {
                "stream_id": stream.stream_id,
                "name": stream.name,
                "status": stream.status,
                "fps": stream.fps,
                "frames_processed": stream.frames_processed,
            }
            for stream in self.streams.values()
        ]


# Global stream manager
stream_manager = StreamManager()


# Register VisionEdge camera streams
stream_manager.add_stream(1, "Camera 01")
stream_manager.add_stream(2, "Camera 02")
stream_manager.add_stream(3, "Camera 03")
stream_manager.add_stream(4, "Camera 04")