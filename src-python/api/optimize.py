from __future__ import annotations

from pathlib import Path

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
