from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "router": "sources"}


@router.get("/detected")
async def detected_sources():
    home = Path.home()
    detected = []

    icloud = home / "Library/Mobile Documents/com~apple~CloudDocs"
    if icloud.exists():
        detected.append({"type": "icloud", "label": "iCloud Drive", "path": str(icloud)})

    cloud_storage = home / "Library/CloudStorage"
    if cloud_storage.exists():
        for entry in cloud_storage.iterdir():
            if entry.is_dir() and entry.name.startswith("GoogleDrive-"):
                email = entry.name[len("GoogleDrive-") :]
                for child in entry.iterdir():
                    if child.is_dir():
                        detected.append(
                            {
                                "type": "gdrive_local",
                                "label": f"Google Drive ({email})",
                                "path": str(child),
                            }
                        )

    dropbox = home / "Dropbox"
    if dropbox.exists():
        detected.append({"type": "local", "label": "Dropbox", "path": str(dropbox)})

    onedrive = home / "OneDrive"
    if onedrive.exists():
        detected.append({"type": "local", "label": "OneDrive", "path": str(onedrive)})

    for folder_name in ("Downloads", "Documents", "Desktop", "Pictures"):
        folder = home / folder_name
        if folder.exists():
            detected.append({"type": "local", "label": folder_name, "path": str(folder)})

    return {"sources": detected}


@router.get("/locations")
async def common_scan_locations():
    home = Path.home()
    candidates = [
        home,
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Pictures",
        home / "Library" / "CloudStorage",
        Path("/Volumes"),
    ]
    if Path("/Volumes").exists():
        candidates.extend(path for path in Path("/Volumes").iterdir() if path.is_dir())

    seen = set()
    locations = []
    for candidate in candidates:
        path = str(candidate)
        if path in seen or not candidate.exists():
            continue
        seen.add(path)
        locations.append({"label": candidate.name or path, "path": path})
    return {"locations": locations}


class RevealRequest(BaseModel):
    path: str = Field(min_length=1)


@router.post("/reveal")
async def reveal(req: RevealRequest):
    target = Path(req.path).expanduser().resolve()
    if sys.platform == "darwin":
        command = ["open", "-R", str(target)]
    elif sys.platform.startswith("win"):
        command = ["explorer", f"/select,{target}"]
    else:
        folder = target if target.is_dir() else target.parent
        command = ["xdg-open", str(folder)]
    subprocess.Popen(command)
    return {"status": "opened"}
