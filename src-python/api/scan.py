from __future__ import annotations

import asyncio
import threading
import time
import uuid

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from cloudsaver.audit import build_storage_audit
from cloudsaver.duplicates import attach_duplicate_verification
from cloudsaver.optimize import attach_reduction_estimates
from cloudsaver.provider_adapters import ProviderScanContext
from cloudsaver.provider_registry import get_provider_adapter
from cloudsaver.scan import scan_local_folder

router = APIRouter()
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


class ScanRequest(BaseModel):
    path: str = Field(min_length=1)
    quality: int = 82
    max_width: int = 1920
    max_height: int = 1080
    exclude_globs: list[str] = []
    annotate_icloud: bool = False


class ProviderScanRequest(BaseModel):
    source_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    path: str | None = None
    access_token: str | None = None
    quality: int = 82
    max_width: int = 1920
    max_height: int = 1080
    exclude_globs: list[str] = []


@router.get("/health")
async def health():
    return {"status": "ok", "router": "scan"}


@router.post("/local/start")
async def start_local_scan(req: ScanRequest):
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "source_type": "local",
            "files_scanned": 0,
            "current_path": "",
            "stage": "Waiting",
            "created_at": time.time(),
            "started_at": None,
            "updated_at": time.time(),
        }
    threading.Thread(target=_run_local_scan, args=(job_id, req), daemon=True).start()
    return {"job_id": job_id, "status": "queued"}


@router.post("/provider/start")
async def start_provider_scan(req: ProviderScanRequest):
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "source_type": req.source_type,
            "source_id": req.source_id,
            "files_scanned": 0,
            "current_path": "",
            "stage": "Waiting",
            "created_at": time.time(),
            "started_at": None,
            "updated_at": time.time(),
        }
    threading.Thread(target=_run_provider_scan, args=(job_id, req), daemon=True).start()
    return {"job_id": job_id, "status": "queued"}


@router.get("/{job_id}")
async def get_job(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {key: value for key, value in job.items() if key != "result"}


@router.websocket("/{job_id}/ws")
async def job_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(0.25)
            with _jobs_lock:
                job = dict(_jobs.get(job_id, {}))
            status = job.get("status", "unknown")
            message = {key: value for key, value in job.items() if key != "result"}
            if status == "complete":
                message["result"] = job.get("result")
            await websocket.send_json(message)
            if status in ("complete", "failed"):
                break
    except WebSocketDisconnect:
        pass


def job_snapshot(job_id: str) -> dict | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def _update_job(job_id: str, updates: dict):
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(updates)
            _jobs[job_id]["updated_at"] = time.time()


def _run_local_scan(job_id: str, req: ScanRequest):
    def on_progress(progress: dict):
        _update_job(
            job_id,
            {
                "status": "scanning",
                "stage": "Reading files",
                "files_scanned": progress.get("files_scanned", 0),
                "current_path": progress.get("current_path", ""),
            },
        )

    _update_job(job_id, {"status": "scanning", "stage": "Reading files", "started_at": time.time()})
    try:
        files = scan_local_folder(
            req.path,
            progress_callback=on_progress,
            exclude_globs=req.exclude_globs,
        )
        if req.annotate_icloud:
            _update_job(job_id, {"stage": "Checking iCloud state"})
            from api.icloud import get_icloud_file_state

            for file in files:
                file["icloud_state"] = get_icloud_file_state(file.get("path", ""))
        _update_job(job_id, {"stage": "Hashing duplicates"})
        files = attach_duplicate_verification(files)
        _update_job(job_id, {"stage": "Estimating savings"})
        files = attach_reduction_estimates(files, (req.max_width, req.max_height), req.quality)
        _update_job(job_id, {"stage": "Building audit"})
        audit = build_storage_audit(files)
        files.sort(key=lambda file: file["size_bytes"], reverse=True)
        result = {"root_path": req.path, "audit": audit, "files": files}
        started_at = (job_snapshot(job_id) or {}).get("started_at") or time.time()
        duration = time.time() - float(started_at)
        notification_body = f"{len(files)} files scanned in {duration:.0f}s"
        complete_updates = {
            "status": "complete",
            "stage": "Complete",
            "files_scanned": len(files),
            "result": result,
        }
        if duration > 30:
            complete_updates.update(
                {
                    "notify": True,
                    "notification_body": notification_body,
                }
            )
        _update_job(
            job_id,
            complete_updates,
        )
    except Exception as error:
        _update_job(job_id, {"status": "failed", "error": str(error)})


def _run_provider_scan(job_id: str, req: ProviderScanRequest):
    def on_progress(progress: dict):
        _update_job(
            job_id,
            {
                "status": "scanning",
                "stage": "Reading provider files",
                "files_scanned": progress.get("files_scanned", 0),
                "current_path": progress.get("current_path", ""),
            },
        )

    _update_job(
        job_id,
        {"status": "scanning", "stage": "Connecting provider", "started_at": time.time()},
    )
    try:
        adapter = get_provider_adapter(req.source_type)
        context = ProviderScanContext(
            source_id=req.source_id,
            source_type=req.source_type,
            path=req.path,
            access_token=req.access_token,
            options={"exclude_globs": req.exclude_globs},
        )
        provider_files = list(adapter.scan(context, progress_callback=on_progress))
        files = [file.to_scan_dict() for file in provider_files]
        _update_job(job_id, {"stage": "Hashing duplicates"})
        files = attach_duplicate_verification(files)
        _update_job(job_id, {"stage": "Estimating savings"})
        files = attach_reduction_estimates(files, (req.max_width, req.max_height), req.quality)
        _update_job(job_id, {"stage": "Building audit"})
        audit = build_storage_audit(files)
        files.sort(key=lambda file: file["size_bytes"], reverse=True)
        result = {
            "source_id": req.source_id,
            "source_type": req.source_type,
            "root_path": req.path,
            "audit": audit,
            "files": files,
        }
        _update_job(
            job_id,
            {
                "status": "complete",
                "stage": "Complete",
                "files_scanned": len(files),
                "result": result,
            },
        )
    except Exception as error:
        _update_job(job_id, {"status": "failed", "error": str(error)})
