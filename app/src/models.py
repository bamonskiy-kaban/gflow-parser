from pydantic import BaseModel
from typing import Optional, List


class TargetInfoRequest(BaseModel):
    relative_target_path: str


class TargetInfo(BaseModel):
    os: str
    hostname: str
    domain: Optional[str]
    version: Optional[str]
    ips: List[str]


class TaskResult(BaseModel):
    error: Optional[str]
    processing_error: Optional[str]
    records_count: Optional[int]
    execution_time: Optional[float]
    is_ready: bool


class TaskDescriptor(BaseModel):
    task_id: str
    function_name: str


class TargetProcessingRequest(BaseModel):
    index: str
    functions_preset: str
    relative_target_path: str
