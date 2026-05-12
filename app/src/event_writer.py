from contextlib import AbstractAsyncContextManager
from typing import Optional
from datetime import datetime

import logging
import asyncio

logger = logging.getLogger(__name__)


class EvidenceJsonRecordPacker:
    def __init__(self, processing_id: str, index: str, function_name: str):
        self.meta = {
            "processing_id": processing_id,
            "index": index,
            "function_name": function_name
        }

    def pack_obj(self, obj: Any):
        if isinstance(obj, Record):
            serial = obj._asdict()

            serial["_type"] = "record"
            serial["_recorddescriptor"] = obj._desc.identifier

            for field_type, field_name in obj._desc.get_field_tuples():
                # Boolean field types should be cast to a bool instead of staying ints
                if field_type == "boolean" and isinstance(serial[field_name], int):
                    serial[field_name] = bool(serial[field_name])

            serial["meta"] = self.meta

            return serial
        if isinstance(obj, RecordDescriptor):
            return {
                "_type": "recorddescriptor",
                "_data": obj._pack(),
            }
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, fieldtypes.digest):
            return {
                "md5": obj.md5,
                "sha1": obj.sha1,
                "sha256": obj.sha256,
            }
        if isinstance(obj, (fieldtypes.net.ipaddress, fieldtypes.net.ipnetwork, fieldtypes.net.ipinterface)):
            return str(obj)
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode()
        if isinstance(obj, fieldtypes.path):
            return str(obj)
        if isinstance(obj, fieldtypes.command):
            return {
                "executable": obj.executable,
                "args": obj.args,
            }

        raise TypeError(f"Unpackable type {type(obj)}")

    def pack(self, obj: Any):
        return orjson.dumps(obj, default=self.pack_obj)



class AsyncTcpEventWriter(AbstractAsyncContextManager):
    def __init__(self,
                 broker_host: str,
                 broker_port: int,
                 batch_max_size: int = 1000,
                 max_queue_size: int = 20000,
                 retry_delay: int = 2
                 ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.batch_max_size = batch_max_size
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
        try:
            while not (self._is_closing and self._queue.empty()):
                try:
                    first_event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                batch = [first_event]
                try:
                    while len(batch) < self.batch_max_size:
                        batch.append(self._queue.get_nowait())
                except asyncio.QueueEmpty:
                    pass
                chunk = b'\n'.join(batch) + b'\n'
                await self._send_chunk_with_retry(chunk)
                for _ in range(len(batch)): self._queue.task_done()

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
