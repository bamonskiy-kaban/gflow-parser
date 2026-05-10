from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from models import (
    Base,
    EvidencePostRequest,
    EvidenceResponse,
    Evidence,
    TaskResult,
    Task
)

from broker import broker
from config import API_TARGETS_DIR, FUNCTIONS

from tasks import process_function
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from helpers import get_target_info, validate_index

import uuid
import datetime
import os


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    if not broker.is_worker_process:
        await broker.startup()
    yield
    if not broker.is_worker_process:
        await broker.shutdown()


app = FastAPI(lifespan=lifespan)
Base.metadata.create_all(bind=engine)


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/evidence")
async def create_evidence(request: EvidencePostRequest, db: Session = Depends(get_db)):
    file_path = os.path.join(API_TARGETS_DIR, request.relative_file_path)

    if not os.path.exists(file_path):
        raise HTTPException(400, "No such file")

    if not file_path.endswith(".tar"):
        raise HTTPException(400, "Supported .TAR only")

    if not validate_index(request.index):
        raise HTTPException(400, "Invalid index name")

    try:
        target_info = get_target_info(file_path)

    except Exception as e:
        raise HTTPException(500, f"Evidence handling error: {str(e)}")

    evidence_id = uuid.uuid4().hex
    functions = FUNCTIONS.get(target_info.os)

    if not functions:
        raise HTTPException(400, f"No functions for target [{request.relative_file_path}]. OS: [{target_info.os}]")

    evidence = Evidence(
        evidence_id=evidence_id,
        hostname=target_info.hostname,
        domain=target_info.domain,
        index=request.index,
        storage_path=file_path,
        os=target_info.os,
        os_version=target_info.version,
        ips=target_info.ips,
        created_at=datetime.datetime.now()
    )
    db.add(evidence)

    tasks = []
    for function in functions:
        task = await process_function.kiq(request.index, evidence_id, file_path, function)
        tasks.append(
            Task(
                task_id=task.task_id,
                evidence_id=evidence.evidence_id,
                name=function
            )
        )

    db.add_all(tasks)
    db.commit()
    db.refresh(evidence)

    return {"evidence_id": evidence_id}


@app.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(404, "Evidence not found")

    tasks = db.query(Task).filter(Task.evidence_id == evidence_id).all()
    task_ids = [t.task_id for t in tasks]
    ips = str(evidence.ips).split(",")

    return EvidenceResponse(
        evidence_id=evidence.evidence_id,
        index=evidence.index,
        hostname=evidence.hostname,
        domain=evidence.domain,
        os=evidence.os,
        os_version=evidence.os_version,
        ips=ips,
        created_at=evidence.created_at,
        tasks=task_ids
    )


@app.get("/task/{task_id}", response_model=TaskResult)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")

    is_ready = await broker.result_backend.is_result_ready(task_id)
    task_result = await broker.result_backend.get_result(task_id) if is_ready else None

    processing_error = None
    records_count = None

    if task_result:
        if task_result.return_value:
            processing_error = task_result.return_value.get("processing_error")
            records_count = task_result.return_value.get("records")

    return TaskResult(
        name=task.name,
        error=str(task_result.error) if task_result else None,
        processing_error=processing_error,
        records_count=records_count,
        execution_time=task_result.execution_time if task_result else None,
        is_ready=is_ready
    )
