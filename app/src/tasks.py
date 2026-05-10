from broker import broker

from dissect.target.target import Target
from flow.record import iter_timestamped_records, Record, RecordDescriptor, fieldtypes

from event_writer import AsyncTcpEventWriter
from typing import Any
from config import EVENT_BROKER_HOST, EVENT_BROKER_PORT
from datetime import datetime

from typing import Dict
from pathlib import Path

import orjson
import base64
import logging

logger = logging.getLogger(__name__)

TARGET_ROOT = "/targets"


class InvalidBrokerConfigException(Exception):
    pass


class EvidenceJsonRecordPacker:
    def __init__(self, evidence_id: str, index: str):
        self.evidence_id = evidence_id
        self.index = index

    def pack_obj(self, obj: Any):
        if isinstance(obj, Record):
            serial = obj._asdict()

            serial["_type"] = "record"
            serial["_recorddescriptor"] = obj._desc.identifier

            for field_type, field_name in obj._desc.get_field_tuples():
                # Boolean field types should be cast to a bool instead of staying ints
                if field_type == "boolean" and isinstance(serial[field_name], int):
                    serial[field_name] = bool(serial[field_name])

            serial["evidence_id"] = self.evidence_id
            serial["idx"] = self.index

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


@broker.task
async def process_function(index: str,
                           evidence_id: str,
                           relative_path: str,
                           function_name: str) -> Dict:
    logger.info(
        f"Function [{function_name}] execution initialized for evidence [{evidence_id}]. Target [{relative_path}]")

    result_dict = {
        "records": 0,
        "processing_error": None
    }

    tcp_event_broker_host = EVENT_BROKER_HOST
    tcp_event_broker_port = EVENT_BROKER_PORT

    if not (tcp_event_broker_port or tcp_event_broker_host):
        raise InvalidBrokerConfigException(
            f"Fatal error. Broker host: [{tcp_event_broker_host}] | Broker port: [{str(tcp_event_broker_port)}]")

    target_path = Path(TARGET_ROOT) / relative_path
    target = Target.open(target_path)

    _, function = target.get_function(function_name)

    count = 0
    record_packer = EvidenceJsonRecordPacker(evidence_id, index)

    logger.info(
        f"Started function [{function_name}] execution for evidence [{evidence_id}]. Target full path: [{target_path}]")

    try:
        async with AsyncTcpEventWriter(tcp_event_broker_host, tcp_event_broker_port) as event_writer:
            for rec in function():
                for record in iter_timestamped_records(rec):
                    event = record_packer.pack(record)
                    await event_writer.write_event(event)
                    count += 1

    except Exception as e:
        logger.critical(f"Processing critical error: [{e}]", exc_info=True)
        result_dict["processing_error"] = str(e)

    finally:
        logger.info(
            f"Processing completed. Target info - Evidence UID: [{evidence_id}] | Target path: [{target_path}] | Function: [{function_name}] | Records: [{count}]")
        result_dict["records"] = count
        return result_dict
