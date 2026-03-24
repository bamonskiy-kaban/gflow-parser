from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from enum import Enum
from pydantic import BaseModel
from taskiq_redis.exceptions import ResultIsMissingError

from broker import broker
from config import EVENT_BROKER_HOST, EVENT_BROKER_PORT
from tasks import process_function
from helpers import create_index

import uuid


class FunctionProcessingTask(BaseModel):
    target_path: str
    function: str


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    if not broker.is_worker_process:
        await broker.startup()
    yield
    if not broker.is_worker_process:
        await broker.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post("/tasks")
async def create_evidence_processing_task(task: FunctionProcessingTask):
    evidence_id = uuid.uuid4().hex
    try:
        await create_index(evidence_id)
    except Exception as e:
        return {
            "status": "failed",
            "evidence_uid": evidence_id,
            "error": str(e)
        }

    task = await process_function.kiq(evidence_id, task.target_path, task.function, EVENT_BROKER_HOST,
                                      EVENT_BROKER_PORT)
    return {
        "task_id": task.task_id,
        "evidence_uid": evidence_id,
        "status": "Enqueued"
    }


@app.get("/tasks/{task_id}")
async def get_task_results(task_id: str):
    is_ready = await broker.result_backend.is_result_ready(task_id)

    if not is_ready:
        return {"task_id": task_id, "status": "not ready"}

    task_result = await broker.result_backend.get_result(task_id)
    return {
        "task_id": task_id,
        "is_crashed": task_result.is_err,
        "result": task_result.return_value if not task_result.is_err else None,
        "error_msg": str(task_result.error) if task_result.is_err else None,
        "executed_in": task_result.execution_time
    }
