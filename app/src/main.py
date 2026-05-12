from fastapi import FastAPI, HTTPException

from broker import broker
from models import (
    TargetProcessingRequest,
    TaskResult,
    TaskDescriptor,
    TargetInfo,
    TargetInfoRequest
)

from typing import List
from dissect.target.target import Target
from config import API_TARGETS_DIR, FUNCTIONS

from tasks import process_function

import os


def acquire_target_info(target_path: str) -> TargetInfo:
    target = Target.open(target_path)

    if not hasattr(target, "os"):
        raise Exception(f"No OS plugin found for target: {target_path}")

    if not hasattr(target, "hostname"):
        raise Exception(f"No hostname found for target: {target_path}")

    hostname = getattr(target, "hostname")
    domain = getattr(target, "domain") if hasattr(target, "domain") else None

    host_os = getattr(target, "os")
    version = getattr(target, "version") if hasattr(target, "version") else None
    ips = getattr(target, "ips") if hasattr(target, "ips") else []

    return TargetInfo(
        os=host_os,
        hostname=hostname,
        domain=domain,
        version=version,
        ips=ips
    )


app = FastAPI()


@app.get("/target_info", response_model=TargetInfo)
async def get_target_info(request: TargetInfoRequest):
    target_path = os.path.join(API_TARGETS_DIR, request.relative_target_path)
    return acquire_target_info(target_path)


@app.post("/process_target", response_model=List[TaskDescriptor])
async def run_target_processing(request: TargetProcessingRequest):
    file_path = os.path.join(API_TARGETS_DIR, request.relative_target_path)

    if not os.path.exists(file_path):
        raise HTTPException(400, "No such file")

    if not file_path.endswith(".tar"):
        raise HTTPException(400, "Supported .TAR only")

    functions = FUNCTIONS.get(request.functions_preset)
    if not functions:
        raise HTTPException(400,
                            f"No functions for target [{request.relative_target_path}]. Functions preset: [{request.functions_preset}]")

    tasks = []
    for function in functions:
        task = await process_function.kiq(request.index, file_path, function)
        tasks.append(
            TaskDescriptor(
                task_id=task.task_id,
                function_name=function
            )
        )

    return tasks


@app.get("/task/{task_id}", response_model=TaskResult)
async def get_task(task_id: str):
    is_ready = await broker.result_backend.is_result_ready(task_id)
    task_result = await broker.result_backend.get_result(task_id) if is_ready else None

    processing_error = None
    records_count = None

    if task_result and hasattr(task_result, "return_value"):
        if task_result.return_value:
            processing_error = task_result.return_value.get("processing_error")
            records_count = task_result.return_value.get("records")

    return TaskResult(
        error=str(task_result.error) if task_result and hasattr(task_result, "error") else None,
        processing_error=processing_error,
        records_count=records_count,
        execution_time=task_result.execution_time if task_result and hasattr(task_result, "execution_time") else None,
        is_ready=is_ready
    )
