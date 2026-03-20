import asyncio
import json
import logging
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


class SSEManager:
    """Manages SSE connections for upload status updates.

    Supports publishing from synchronous threads (background jobs)
    to asyncio queues consumed by SSE endpoints.
    """

    def __init__(self):
        self._queues: dict[str, list[tuple[asyncio.Queue, asyncio.AbstractEventLoop]]] = defaultdict(list)
        self._lock = Lock()

    def subscribe(self, upload_id: str) -> asyncio.Queue:
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self._queues[upload_id].append((queue, loop))
        logger.info("SSE client subscribed to upload_id=%s", upload_id)
        return queue

    def unsubscribe(self, upload_id: str, queue: asyncio.Queue) -> None:
        with self._lock:
            if upload_id in self._queues:
                self._queues[upload_id] = [
                    (q, loop) for q, loop in self._queues[upload_id] if q is not queue
                ]
                if not self._queues[upload_id]:
                    del self._queues[upload_id]
        logger.info("SSE client unsubscribed from upload_id=%s", upload_id)

    def publish(self, upload_id: str, data: dict) -> None:
        """Publish event to all subscribers. Thread-safe, works from sync threads."""
        message = json.dumps(data)
        with self._lock:
            entries = list(self._queues.get(upload_id, []))

        for queue, loop in entries:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, message)
            except RuntimeError:
                logger.warning("Event loop closed for upload_id=%s", upload_id)

        if entries:
            logger.info(
                "SSE published to %d clients for upload_id=%s", len(entries), upload_id
            )


sse_manager = SSEManager()
