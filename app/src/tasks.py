from broker import broker

from dissect.target.target import Target
from flow.record import iter_timestamped_records, RecordDescriptor
from serialization import JsonRecordPackerWrapper

from event_writer import AsyncTcpEventWriter
from typing import Any
from config import EVENT_BROKER_HOST, EVENT_BROKER_PORT

from typing import Dict
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

TARGET_ROOT = "/targets"


class InvalidBrokerConfigException(Exception):
    pass


@broker.task
async def process_function(index: str,
                           relative_path: str,
                           function_name: str) -> Dict:
    logger.info(
        f"Function [{function_name}] execution initialized for processing index [{index}]. Target [{relative_path}]")

    result_dict = {
        "records": 0,
        "processing_error": ""
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
    record_packer = JsonRecordPackerWrapper(index, function_name)

    logger.info(
        f"Started function [{function_name}] execution for index [{index}]. Target full path: [{target_path}]")

    try:
        async with AsyncTcpEventWriter(tcp_event_broker_host, tcp_event_broker_port) as event_writer:
            for rec in function():
                if isinstance(rec, RecordDescriptor):
                    continue

                for record in iter_timestamped_records(rec):
                    event = record_packer.pack(record)
                    await event_writer.write_event(event)
                    count += 1

    except Exception as e:
        logger.critical(f"Processing critical error: [{e}]", exc_info=True)
        result_dict["processing_error"] = str(e)

    finally:
        logger.info(
            f"Processing completed. Target info - Index: [{index}] | Target path: [{target_path}] | Function: [{function_name}] | Records: [{count}]")
        result_dict["records"] = count
        return result_dict
