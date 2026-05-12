from flow.record import Record, JsonRecordPacker, fieldtypes
from typing import Any

import orjson


class JsonRecordPackerWrapper:
    def __init__(self, processing_id: str, function_name: str):
        self.meta = {
            "processing_id": processing_id,
            "function_name": function_name
        }
        self.packer = JsonRecordPacker()

    def pack_obj(self, obj: Any):
        if isinstance(obj, fieldtypes.command):
            return f"{obj.executable} {' '.join(obj.args)}"

        result = self.packer.pack_obj(obj)
        if isinstance(obj, Record):
            result["meta"] = self.meta
        return result

    def pack(self, obj: Any):
        return orjson.dumps(obj, default=self.pack_obj, option=orjson.OPT_APPEND_NEWLINE)
