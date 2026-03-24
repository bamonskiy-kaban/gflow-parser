import asyncio
import orjson

from broker import broker

from dissect.target.target import Target
from flow.record import JsonRecordPacker, iter_timestamped_records

from contextlib import AbstractAsyncContextManager
from typing import Optional, Dict
import abc


class AbstractAsyncEventWriter(abc.ABC):
    @abc.abstractmethod
    async def write_event(self, event_bytes):
        pass

    @abc.abstractmethod
    async def flush(self):
        pass


class AsyncTcpEventWriter(AbstractAsyncContextManager, AbstractAsyncEventWriter):
    def __init__(self, logstash_host: str, logstash_port: int, buffer_size: int = 25000):
        self.logstash_host = logstash_host
        self.logstash_port = logstash_port
        self.buffer_size = buffer_size

        self._chunk = bytearray()
        self._events_count = 0
        self._writer: Optional[asyncio.StreamWriter] = None

    async def write_event(self, event_bytes):
        self._chunk.extend(event_bytes + b'\n')
        self._events_count += 1
        if self._events_count > self.buffer_size:
            await self.flush()

    async def flush(self):
        if not self._events_count:
            return

        try:
            if not self._writer:
                _, self._writer = await asyncio.open_connection(self.logstash_host, self.logstash_port)

            elif self._writer.is_closing():
                await self._writer.wait_closed()
                _, self._writer = await asyncio.open_connection(self.logstash_host, self.logstash_port)

            self._writer.write(self._chunk.copy())
            await self._writer.drain()

            self._chunk.clear()
            self._events_count = 0

        finally:
            self._chunk.clear()
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.flush()


@broker.task
async def process_function(evidence_uid: str,
                           target_path: str,
                           function: str,
                           tcp_event_broker_host: str,
                           tcp_event_broker_port: int) -> Dict:
    result_dict = {
        "evidence_uid": evidence_uid,
        "evidence_path": target_path,
        "function_name": function,
        "records": 0,
        "error": None
    }

    try:
        target = Target.open(target_path)
    except Exception as e:
        result_dict["error"] = str(e)
        return result_dict

    if not target.has_function(function):
        result_dict["error"] = "No such function"
        return result_dict

    _, function = target.get_function(function)

    count = 0
    record_packer = JsonRecordPacker()

    try:
        async with AsyncTcpEventWriter(tcp_event_broker_host, tcp_event_broker_port) as event_writer:
            for rec in function():
                for record in iter_timestamped_records(rec):
                    event = record_packer.pack_obj(record)
                    event["evidence_uid"] = evidence_uid
                    # event["os"] = getattr(target, "os") if hasattr(target, "os") else None
                    # event["ips"] = getattr(target, "ips") if hasattr(target, "ips") else None
                    # event["os_version"] = getattr(target, "version") if hasattr(target, "version") else None
                    await event_writer.write_event(orjson.dumps(event, default=record_packer.pack_obj))
                    count += 1

    except Exception as e:
        result_dict["error"] = str(e)

    finally:
        result_dict["records"] = count
        return result_dict
