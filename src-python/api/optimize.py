from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from fastapi import APIRouter
from pydantic import BaseModel, Field

from cloudsaver.optimize import (
    DEFAULT_IMAGE_QUALITY,
    HD_RESOLUTION,
    REDUCED_DIR,
    convert_image_format,
    optimize_png_lossless,
    reduce_selected_images,
)
from cloudsaver.quarantine import quarantine_selected_files
from cloudsaver.scan import is_path_within

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "router": "optimize"}


class ImageOptimizeRequest(BaseModel):
    root_path: str = Field(min_length=1)
    file_ids: list[str] = Field(min_length=1)
    output_dir: str = REDUCED_DIR
    quality: int = DEFAULT_IMAGE_QUALITY
    max_width: int = HD_RESOLUTION[0]
    max_height: int = HD_RESOLUTION[1]


class ConvertRequest(ImageOptimizeRequest):
    target_format: str = "webp"


class MediaEncodeRequest(BaseModel):
    root_path: str = Field(min_length=1)
    file_ids: list[str] = Field(min_length=1)
    preset: str = "hevc"


@router.post("/images")
async def optimize_images(req: ImageOptimizeRequest):
    return reduce_selected_images(
        root_path=req.root_path,
        file_ids=req.file_ids,
        output_dir=req.output_dir,
        max_resolution=(req.max_width, req.max_height),
        quality=req.quality,
    )


@router.post("/convert")
async def convert_images(req: ConvertRequest):
    return convert_image_format(
        root_path=req.root_path,
        file_ids=req.file_ids,
        target_format=req.target_format,
        output_dir=req.output_dir,
        max_resolution=(req.max_width, req.max_height),
        quality=req.quality,
    )


@router.post("/png")
async def optimize_png(req: ImageOptimizeRequest):
    root = Path(req.root_path).expanduser().resolve()
    results = []
    for file_id in req.file_ids:
        path = (root / file_id).resolve()
        if not is_path_within(path, root):
            results.append({"id": file_id, "status": "skipped", "error": "Path is outside scan root."})
            continue
        if not path.exists() or not path.is_file() or path.suffix.lower() != ".png":
            results.append({"id": file_id, "status": "skipped", "error": "PNG file not found."})
            continue
        try:
            before, after = optimize_png_lossless(path)
        except RuntimeError as error:
            results.append({"id": file_id, "status": "unavailable", "error": str(error)})
            continue
        results.append(
            {
                "id": file_id,
                "status": "optimized",
                "before_bytes": before,
                "after_bytes": after,
                "saved_bytes": max(before - after, 0),
            }
        )
    return {"results": results}


@router.get("/ffmpeg")
async def ffmpeg_status():
    return {"available": shutil.which("ffmpeg") is not None}


@router.post("/video/reencode")
async def reencode_video(req: MediaEncodeRequest):
    return _encode_media(req, kind="video")


@router.post("/audio/opus")
async def convert_audio_opus(req: MediaEncodeRequest):
    return _encode_media(req, kind="audio")


def _encode_media(req: MediaEncodeRequest, kind: str) -> dict:
    if not shutil.which("ffmpeg"):
        return {"results": [{"status": "unavailable", "error": "ffmpeg not found"}]}

    root = Path(req.root_path).expanduser().resolve()
    results = []
    for file_id in req.file_ids:
        source = (root / file_id).resolve()
        if not is_path_within(source, root) or not source.exists():
            results.append({"id": file_id, "status": "skipped", "error": "File not found"})
            continue

        quarantine = quarantine_selected_files(str(root), [file_id])
        moved = next(
            (item for item in quarantine["results"] if item.get("status") == "quarantined"),
            None,
        )
        if not moved:
            results.append({"id": file_id, "status": "skipped", "error": "Could not move original to review"})
            continue

        review_path = Path(moved["review_path"])
        output = source.with_suffix(".hevc.mp4" if kind == "video" else ".opus.ogg")
        command = (
            [
                "ffmpeg",
                "-i",
                str(review_path),
                "-c:v",
                "libx265",
                "-crf",
                "28",
                "-c:a",
                "copy",
                "-y",
                str(output),
            ]
            if kind == "video"
            else [
                "ffmpeg",
                "-i",
                str(review_path),
                "-c:a",
                "libopus",
                "-b:a",
                "128k",
                "-y",
                str(output),
            ]
        )
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=3600)
            results.append({"id": file_id, "status": "encoded", "output": str(output)})
        except Exception as error:
            results.append({"id": file_id, "status": "failed", "error": str(error)})
    return {"results": results}
