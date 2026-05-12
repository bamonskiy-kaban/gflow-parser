from flow.record import Record, JsonRecordPacker
from typing import Any

import orjson


class JsonRecordPackerWrapper:
    def __init__(self, index: str, function_name: str):
        self.meta = {
            "index": index,
            "function_name": function_name
        }
        self.packer = JsonRecordPacker()

    def pack_obj(self, obj: Any):
        result = self.packer.pack_obj(obj)
        if isinstance(obj, Record):
            result["meta"] = self.meta
        return result

    def pack(self, obj: Any):
        return orjson.dumps(obj, default=self.pack_obj, option=orjson.OPT_APPEND_NEWLINE)
