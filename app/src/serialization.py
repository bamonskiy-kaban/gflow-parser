from flow.record import Record, JsonRecordPacker
from typing import Any

import orjson


class JsonRecordPackerWrapper:
    def __init__(self, processing_id: str, function_name: str):
        self.meta = {
            "processing_id": processing_id,
            "function_name": function_name
        }
        self.packer = JsonRecordPacker()

    # TODO: fix fieldtypes.command type serialization
    def pack_obj(self, obj: Any):
        result = self.packer.pack_obj(obj)
        if isinstance(obj, Record):
            result["meta"] = self.meta
        return result

    def pack(self, obj: Any):
        return orjson.dumps(obj, default=self.pack_obj, option=orjson.OPT_APPEND_NEWLINE)
