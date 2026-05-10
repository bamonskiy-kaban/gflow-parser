from contextlib import AbstractAsyncContextManager
from typing import Optional

import logging
import asyncio

logger = logging.getLogger(__name__)


class AsyncTcpEventWriter(AbstractAsyncContextManager):
    def __init__(self,
                 broker_host: str,
                 broker_port: int,
                 buffer_size: int = 10000,
                 max_queue_size: int = 50000,
                 retry_delay: int = 2
                 ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.buffer_size = buffer_size
        self.retry_delay = retry_delay

        self._queue = asyncio.Queue(maxsize=max_queue_size)
        self._worker_task: Optional[asyncio.Task] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._is_closing = False

    async def _connect(self):
        if not self._writer or self._writer.is_closing():
            if self._writer:
                await self._writer.wait_closed()
            _, self._writer = await asyncio.open_connection(self.broker_host, self.broker_port)

    async def _flush_worker(self):
        chunk = bytearray()
        events_count = 0

        try:
            while True:
                try:
                    event_bytes = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                    chunk.extend(event_bytes)
                    chunk.append(10)
                    events_count += 1

                    if events_count >= self.buffer_size:
                        await self._send_chunk_with_retry(chunk)
                        for _ in range(events_count): self._queue.task_done()
                        chunk = bytearray()
                        events_count = 0

                except asyncio.TimeoutError:
                    if events_count > 0:
                        await self._send_chunk_with_retry(chunk)
                        for _ in range(events_count): self._queue.task_done()
                        chunk = bytearray()
                        events_count = 0

                    if self._is_closing and self._queue.empty():
                        break

        except Exception as e:
            logger.critical(f"Fatal error in flush worker: [{e}]", exc_info=True)

    async def _send_chunk_with_retry(self, chunk: bytearray):
        while True:
            try:
                await self._connect()
                self._writer.write(chunk)
                await self._writer.drain()
                break

            except Exception as e:
                logger.error(f"Network error while sending to broker: [{str(e)}]")
                await asyncio.sleep(self.retry_delay)

    async def write_event(self, event_bytes):
        if self._is_closing:
            raise RuntimeError("Cannot write to a closed writer")

        await self._queue.put(event_bytes)

    async def __aenter__(self):
        self._worker_task = asyncio.create_task(self._flush_worker())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._is_closing = True
        await self._queue.join()

        if self._worker_task:
            await self._worker_task

        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
