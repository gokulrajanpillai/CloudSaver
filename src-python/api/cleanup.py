from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from cloudsaver.quarantine import quarantine_selected_files, restore_quarantine

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "router": "cleanup"}


class MoveRequest(BaseModel):
    root_path: str = Field(min_length=1)
    file_ids: list[str] = Field(min_length=1)
    quarantine_dir: str | None = None


class RestoreRequest(BaseModel):
    manifest_path: str = Field(min_length=1)


@router.post("/move")
async def move_to_review(req: MoveRequest):
    return quarantine_selected_files(req.root_path, req.file_ids, req.quarantine_dir)


@router.post("/restore")
async def restore(req: RestoreRequest):
    return restore_quarantine(req.manifest_path)
