from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()
ICLOUD_PATHS = {
    "darwin": Path.home() / "Library/Mobile Documents/com~apple~CloudDocs",
    "windows": Path.home() / "iCloudDrive",
}


@router.get("/health")
async def health():
    return {"status": "ok", "router": "icloud"}


def icloud_root() -> Path | None:
    path = ICLOUD_PATHS.get(platform.system().lower())
    return path if path and path.exists() else None


def get_icloud_file_state(path: str) -> str:
    if platform.system() != "Darwin":
        return "local"
    try:
        result = subprocess.run(
            ["brctl", "log", "-w", "0", path],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        output = result.stdout + result.stderr
        if "evicted" in output.lower():
            return "evicted"
        if "downloading" in output.lower():
            return "downloading"
    except Exception:
        pass

    try:
        import xattr

        attrs = xattr.listxattr(path)
        if b"com.apple.icloud.presence" in attrs or "com.apple.icloud.presence" in attrs:
            value = xattr.getxattr(path, "com.apple.icloud.presence")
            if value == b"\x00":
                return "evicted"
    except Exception:
        pass
    return "local"


@router.get("/root")
async def get_icloud_root():
    root = icloud_root()
    return {"path": str(root) if root else None, "available": root is not None}


@router.post("/scan/start")
async def start_icloud_scan(source_id: str = ""):
    root = icloud_root()
    if not root:
        raise HTTPException(status_code=400, detail="iCloud Drive not available on this system")
    from api.scan import ScanRequest, start_local_scan

    response = await start_local_scan(ScanRequest(path=str(root), annotate_icloud=True))
    return {**response, "source_id": source_id, "source_type": "icloud"}
