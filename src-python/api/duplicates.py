from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib

from fastapi import APIRouter
from pydantic import BaseModel

from cloudsaver.audit import human_readable_size

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "router": "duplicates"}


@dataclass
class UnifiedFile:
    source_id: str
    source_type: str
    file_id: str
    name: str
    size_bytes: int
    sha256: str | None
    md5: str | None
    mtime: float
    path: str | None
    drive_id: str | None
    icloud_state: str | None


class CrossSourceRequest(BaseModel):
    source_results: list[dict]


@router.post("/cross")
async def find_cross_source_duplicates(req: CrossSourceRequest):
    all_files: list[UnifiedFile] = []
    for result in req.source_results:
        for file in result.get("files", []):
            verification = file.get("duplicate_verification") or {}
            all_files.append(
                UnifiedFile(
                    source_id=file.get("source_id", result.get("source_id", "")),
                    source_type=file.get("source_type", "local"),
                    file_id=file.get("id", ""),
                    name=file.get("name", ""),
                    size_bytes=int(file.get("size_bytes", 0) or 0),
                    sha256=verification.get("content_hash"),
                    md5=file.get("md5"),
                    mtime=_mtime(file),
                    path=file.get("path"),
                    drive_id=file.get("drive_id"),
                    icloud_state=file.get("icloud_state"),
                )
            )
    return {"groups": _find_cross_source_groups(all_files)}


def _mtime(file: dict) -> float:
    raw = file.get("mtime") or file.get("atime") or 0
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0
    return 0


def _hash_md5_local(path: str) -> str | None:
    try:
        digest = hashlib.md5()
        with open(path, "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _find_cross_source_groups(files: list[UnifiedFile]) -> list[dict]:
    candidates: dict[tuple[str, int], list[UnifiedFile]] = {}
    for file in files:
        if file.size_bytes <= 0:
            continue
        candidates.setdefault((file.name.lower(), file.size_bytes), []).append(file)

    groups = []
    for (name, size_bytes), candidate_group in candidates.items():
        if len({file.source_id for file in candidate_group}) <= 1:
            continue

        has_drive = any(file.source_type == "google_drive" for file in candidate_group)
        hash_groups: dict[str, list[UnifiedFile]] = {}
        hash_types: dict[str, set[str]] = {}

        for file in candidate_group:
            hash_value = None
            hash_type = ""
            if file.source_type == "google_drive":
                hash_value = file.md5
                hash_type = "md5"
            elif file.icloud_state == "evicted":
                hash_value = None
            elif has_drive and file.path:
                hash_value = _hash_md5_local(file.path)
                hash_type = "md5" if hash_value else ""
            elif file.sha256:
                hash_value = file.sha256
                hash_type = "sha256"

            if hash_value:
                hash_groups.setdefault(hash_value, []).append(file)
                hash_types.setdefault(hash_value, set()).add(hash_type)

        for content_hash, verified_group in hash_groups.items():
            if len({file.source_id for file in verified_group}) <= 1:
                continue
            keep = _cross_source_keep(verified_group)
            recoverable_bytes = sum(
                file.size_bytes for file in verified_group if file.file_id != keep.file_id
            )
            groups.append(
                {
                    "name": name,
                    "size_bytes": size_bytes,
                    "copies": len(verified_group),
                    "recoverable_bytes": recoverable_bytes,
                    "recoverable_human": human_readable_size(recoverable_bytes),
                    "content_hash": content_hash,
                    "confidence": "high" if len(hash_types.get(content_hash, set())) == 1 else "medium",
                    "verification_status": "verified",
                    "recommended_keep": {
                        "source_id": keep.source_id,
                        "source_type": keep.source_type,
                        "file_id": keep.file_id,
                        "path": keep.path,
                    },
                    "files": [_file_to_dict(file) for file in verified_group],
                }
            )

    groups.sort(key=lambda group: group["recoverable_bytes"], reverse=True)
    return groups


def _cross_source_keep(files: list[UnifiedFile]) -> UnifiedFile:
    risky = {"backup", "old", "copy", "tmp", "temp", "archive", "duplicate"}
    source_priority = {"local": 0, "icloud": 1, "gdrive_local": 1, "google_drive": 2}

    def score(file: UnifiedFile) -> tuple:
        path_lower = (file.path or file.name or "").lower()
        risky_count = sum(1 for term in risky if term in path_lower)
        return (
            source_priority.get(file.source_type, 3),
            risky_count,
            -file.mtime,
            len(file.path or ""),
        )

    return min(files, key=score)


def _file_to_dict(file: UnifiedFile) -> dict:
    return {
        "source_id": file.source_id,
        "source_type": file.source_type,
        "file_id": file.file_id,
        "name": file.name,
        "size_bytes": file.size_bytes,
        "path": file.path,
        "drive_id": file.drive_id,
        "mtime": file.mtime,
        "icloud_state": file.icloud_state,
    }
