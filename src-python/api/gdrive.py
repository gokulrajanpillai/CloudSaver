from __future__ import annotations

import asyncio
import threading
import time
import uuid

from fastapi import APIRouter, Header, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from cloudsaver.audit import build_storage_audit

router = APIRouter()
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()
DRIVE_FILE_FIELDS = "files(id,name,size,mimeType,md5Checksum,parents,modifiedTime,trashed,starred)"


@router.get("/health")
async def health():
    return {"status": "ok", "router": "gdrive"}


class DriveScanRequest(BaseModel):
    access_token: str = Field(min_length=1)
    source_id: str = Field(min_length=1)


class DriveTokenRequest(BaseModel):
    access_token: str = Field(min_length=1)


@router.post("/scan/start")
async def start_drive_scan(req: DriveScanRequest):
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "source_type": "google_drive",
            "source_id": req.source_id,
            "files_scanned": 0,
            "current_path": "",
            "stage": "Waiting",
            "created_at": time.time(),
            "updated_at": time.time(),
        }
    threading.Thread(target=_run_drive_scan, args=(job_id, req), daemon=True).start()
    return {"job_id": job_id, "status": "queued"}


@router.websocket("/scan/{job_id}/ws")
async def drive_scan_ws(websocket: WebSocket, job_id: str):
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


@router.delete("/file/{file_id}")
async def trash_file_delete(file_id: str, access_token: str = Header(default="")):
    _trash_drive_file(file_id, access_token)
    return {"status": "trashed", "file_id": file_id}


@router.post("/file/{file_id}/trash")
async def trash_file_post(file_id: str, req: DriveTokenRequest):
    _trash_drive_file(file_id, req.access_token)
    return {"status": "trashed", "file_id": file_id}


@router.post("/file/{file_id}/webview-link")
async def webview_link(file_id: str, req: DriveTokenRequest):
    service = _drive_service(req.access_token)
    file = service.files().get(fileId=file_id, fields="webViewLink").execute()
    return {"webViewLink": file.get("webViewLink")}


def _update_job(job_id: str, updates: dict):
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(updates)
            _jobs[job_id]["updated_at"] = time.time()


def _drive_service(access_token: str):
    if not access_token:
        raise HTTPException(status_code=401, detail="A Google Drive access token is required.")
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    return build("drive", "v3", credentials=Credentials(token=access_token), cache_discovery=False)


def _run_drive_scan(job_id: str, req: DriveScanRequest):
    _update_job(job_id, {"status": "scanning", "stage": "Connecting to Google Drive"})
    try:
        service = _drive_service(req.access_token)
        about = service.about().get(fields="storageQuota,user").execute()
        quota = about.get("storageQuota", {})
        user_email = about.get("user", {}).get("emailAddress", "")

        files = []
        page_token = None
        while True:
            response = (
                service.files()
                .list(
                    pageSize=1000,
                    fields=f"nextPageToken,{DRIVE_FILE_FIELDS}",
                    q="trashed=false",
                    pageToken=page_token,
                )
                .execute()
            )
            batch = response.get("files", [])
            files.extend(_normalize_drive_file(item, req.source_id) for item in batch)
            _update_job(
                job_id,
                {
                    "files_scanned": len(files),
                    "stage": "Listing Drive files",
                    "current_path": batch[-1].get("name", "") if batch else "",
                },
            )
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        audit = build_storage_audit(files)
        result = {
            "source_id": req.source_id,
            "source_type": "google_drive",
            "user_email": user_email,
            "quota": {
                "used": int(quota.get("usage", 0)),
                "total": int(quota.get("limit", 0) or 0),
                "drive_used": int(quota.get("usageInDrive", 0)),
            },
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


def _normalize_drive_file(file: dict, source_id: str) -> dict:
    return {
        "id": file["id"],
        "source_id": source_id,
        "source_type": "google_drive",
        "name": file.get("name", "Untitled"),
        "path": file.get("name"),
        "size_bytes": int(file.get("size", 0) or 0),
        "mimeType": file.get("mimeType", ""),
        "md5": file.get("md5Checksum"),
        "mtime": file.get("modifiedTime"),
        "parents": file.get("parents", []),
        "included": True,
        "drive_id": file["id"],
    }


def _trash_drive_file(file_id: str, access_token: str):
    service = _drive_service(access_token)
    service.files().update(fileId=file_id, body={"trashed": True}).execute()
