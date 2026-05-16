from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import mimetypes
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path
from typing import Callable, Iterable, List

from PIL import Image

from cloudsaver.config import IMAGE_EXPANSION, MEDIA_ANALYSIS, SMART_SCAN_FOUNDATION, app_data_dir
from cloudsaver.history import load_file_cache, prune_file_cache, save_file_cache

# Optional: install with `python -m pip install "cloudsaver[avif]"`.
try:
    import pillow_avif  # noqa: F401

    AVIF_AVAILABLE = True
except ImportError:
    AVIF_AVAILABLE = False

# Optional: install with `python -m pip install "cloudsaver[image_extras]"`.
try:
    import piexif

    PIEXIF_AVAILABLE = True
except ImportError:
    piexif = None
    PIEXIF_AVAILABLE = False

# Optional: install with `python -m pip install "cloudsaver[image_extras]"`.
try:
    import imagehash
    from PIL import Image as _PilImage

    PERCEPTUAL_HASH_AVAILABLE = True
except ImportError:
    imagehash = None
    _PilImage = None
    PERCEPTUAL_HASH_AVAILABLE = False


APP_DATA_DIR = app_data_dir()
OUTPUT_DIR = str(APP_DATA_DIR / "output")
REDUCED_DIR = os.path.join(OUTPUT_DIR, "reduced")
QUARANTINE_DIR_NAME = ".cloudsaver-review"
DEFAULT_EXCLUDED_DIR_NAMES = {
    QUARANTINE_DIR_NAME,
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "__pycache__",
}
DEFAULT_PROTECTED_PATHS = [
    Path("/System"),
    Path("/bin"),
    Path("/sbin"),
    Path("/usr"),
    Path("/etc"),
    Path("/private/etc"),
    Path("/Applications"),
    Path("/Library"),
    Path("C:/Windows"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
]

HD_RESOLUTION = (1920, 1080)
DEFAULT_AUDIT_TOP_N = 10
LARGE_FILE_THRESHOLD_BYTES = 100 * 1024 * 1024
IMAGE_OPTIMIZATION_SAVINGS_RATE = 0.35
CLOUD_STORAGE_COST_PER_GB_MONTH_USD = 0.025
SUPPORTED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
}
if AVIF_AVAILABLE:
    SUPPORTED_IMAGE_MIME_TYPES.add("image/avif")
DEFAULT_IMAGE_QUALITY = 82
HASH_CHUNK_SIZE = 1024 * 1024
OXIPNG_AVAILABLE = shutil.which("oxipng") is not None
FFPROBE_AVAILABLE = shutil.which("ffprobe") is not None


@dataclass
class LocalFile:
    """Simplified representation of a local or mounted filesystem file."""

    id: str
    name: str
    path: str
    size_bytes: int
    mimeType: str
    included: bool
    parents: List[str]


def human_readable_size(size_bytes: int) -> str:
    """Convert byte counts into a human-readable string."""

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def estimate_monthly_storage_cost_usd(
    size_bytes: int, cost_per_gb_month: float = CLOUD_STORAGE_COST_PER_GB_MONTH_USD
) -> float:
    """Estimate monthly cloud storage cost for a byte count."""

    gib = size_bytes / (1024**3)
    return round(gib * cost_per_gb_month, 2)


def is_path_within(child_path: Path, parent_path: Path) -> bool:
    """Return whether ``child_path`` is inside ``parent_path`` after resolving both."""

    try:
        child_path.resolve().relative_to(parent_path.resolve())
        return True
    except ValueError:
        return False


def normalized_protected_paths(protected_paths: Iterable[str | Path] | None = None) -> list[Path]:
    """Return existing protected paths plus caller-supplied protected paths."""

    candidates = list(DEFAULT_PROTECTED_PATHS)
    if protected_paths:
        candidates.extend(Path(path).expanduser() for path in protected_paths)
    normalized = []
    for path in candidates:
        try:
            if path.exists():
                normalized.append(path.resolve())
        except OSError:
            continue
    return normalized


def is_protected_path(path: str | Path, protected_paths: Iterable[str | Path] | None = None) -> bool:
    """Return whether ``path`` is inside a protected folder."""

    candidate = Path(path).expanduser()
    for protected_path in normalized_protected_paths(protected_paths):
        if candidate.resolve() == protected_path or is_path_within(candidate, protected_path):
            return True
    return False


def matches_exclusion(relative_id: str, name: str, exclude_globs: Iterable[str] | None = None) -> bool:
    """Return whether a relative path or file name matches an exclusion glob."""

    patterns = list(exclude_globs or [])
    return any(fnmatch.fnmatch(relative_id, pattern) or fnmatch.fnmatch(name, pattern) for pattern in patterns)


def guess_mime_type(path: Path) -> str:
    """Infer a MIME type from a local file path."""

    mime_type, _ = mimetypes.guess_type(path)
    return mime_type or "application/octet-stream"


def hash_file_sha256(path: str | Path) -> str:
    """Return a SHA-256 digest for a local file."""

    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_file_partial(
    path: str | Path,
    head_bytes: int = 65536,
    tail_bytes: int = 65536,
) -> str:
    """Return a quick SHA-256 digest of the first and last bytes of a file."""

    path = Path(path)
    size = path.stat().st_size
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        head = file.read(head_bytes)
        digest.update(head)
        if size > head_bytes:
            file.seek(max(size - tail_bytes, 0))
            digest.update(file.read(tail_bytes))
    return digest.hexdigest()


def probe_media_file(path: str | Path) -> dict | None:
    """Return ffprobe JSON for a media file, or None when probing is unavailable."""

    if not MEDIA_ANALYSIS or not FFPROBE_AVAILABLE:
        return None
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                "-show_format",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None


def _media_format_size(ffprobe_result: dict | None) -> int:
    if not ffprobe_result:
        return 0
    try:
        return int(float((ffprobe_result.get("format") or {}).get("size") or 0))
    except (TypeError, ValueError):
        return 0


def estimate_video_savings(ffprobe_result: dict | None) -> dict:
    """Estimate video re-encoding savings from ffprobe stream metadata."""

    empty = {
        "codec_name": "",
        "width": None,
        "height": None,
        "bit_rate": None,
        "duration": None,
        "estimated_hevc_savings_bytes": 0,
        "estimated_av1_savings_bytes": 0,
        "transcoding_recommended": False,
        "container_format": "",
    }
    if not ffprobe_result:
        return empty
    streams = ffprobe_result.get("streams") or []
    stream = next((item for item in streams if item.get("codec_type") == "video"), None)
    if not stream:
        return empty
    size_bytes = _media_format_size(ffprobe_result)
    codec = stream.get("codec_name") or ""
    if codec in {"h264", "mpeg4", "wmv1", "wmv2", "wmv3"}:
        hevc_rate = 0.45
    elif codec == "vp9":
        hevc_rate = 0.15
    else:
        hevc_rate = 0
    av1_rate = 0 if codec == "av1" else 0.55
    hevc_savings = int(size_bytes * hevc_rate)
    av1_savings = int(size_bytes * av1_rate)
    return {
        "codec_name": codec,
        "width": stream.get("width"),
        "height": stream.get("height"),
        "bit_rate": stream.get("bit_rate") or (ffprobe_result.get("format") or {}).get("bit_rate"),
        "duration": stream.get("duration") or (ffprobe_result.get("format") or {}).get("duration"),
        "estimated_hevc_savings_bytes": hevc_savings,
        "estimated_av1_savings_bytes": av1_savings,
        "transcoding_recommended": hevc_savings > LARGE_FILE_THRESHOLD_BYTES,
        "container_format": (ffprobe_result.get("format") or {}).get("format_name") or "",
    }


def estimate_audio_savings(ffprobe_result: dict | None) -> dict:
    """Estimate audio re-encoding savings from ffprobe stream metadata."""

    empty = {
        "codec_name": "",
        "sample_rate": None,
        "bit_rate": None,
        "channels": None,
        "duration": None,
        "is_lossless": False,
        "estimated_opus_savings_bytes": 0,
    }
    if not ffprobe_result:
        return empty
    streams = ffprobe_result.get("streams") or []
    stream = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not stream:
        return empty
    codec = stream.get("codec_name") or ""
    size_bytes = _media_format_size(ffprobe_result)
    is_lossless = codec == "flac" or codec == "wav" or codec.startswith("pcm")
    try:
        bit_rate = int(stream.get("bit_rate") or (ffprobe_result.get("format") or {}).get("bit_rate") or 0)
    except (TypeError, ValueError):
        bit_rate = 0
    if is_lossless:
        savings_rate = 0.85
    elif codec != "opus" and bit_rate > 256000:
        savings_rate = 0.40
    else:
        savings_rate = 0
    return {
        "codec_name": codec,
        "sample_rate": stream.get("sample_rate"),
        "bit_rate": bit_rate or None,
        "channels": stream.get("channels"),
        "duration": stream.get("duration") or (ffprobe_result.get("format") or {}).get("duration"),
        "is_lossless": is_lossless,
        "estimated_opus_savings_bytes": int(size_bytes * savings_rate),
    }


def _attach_media_probe(files: list[dict], cache: dict) -> None:
    if not MEDIA_ANALYSIS:
        return
    media_files = [
        file
        for file in files
        if file.get("mimeType", "").startswith(("video/", "audio/"))
    ]
    if not media_files:
        return
    for file in media_files:
        cached = cache.get(file["id"]) if cache else None
        if cached and cached.get("ffprobe_json") and file.get("cached_hash"):
            file["media_probe"] = cached["ffprobe_json"]
    to_probe = [file for file in media_files if "media_probe" not in file]
    if not FFPROBE_AVAILABLE or not to_probe:
        return
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {executor.submit(probe_media_file, file["path"]): file for file in to_probe}
        for future in as_completed(future_map):
            probe = future.result()
            if probe:
                future_map[future]["media_probe"] = probe


def scan_local_folder(
    root_path: str,
    progress_callback: Callable[[dict], None] | None = None,
    use_cache: bool = True,
    cache_db_path: str | Path | None = None,
    exclude_globs: Iterable[str] | None = None,
    protected_paths: Iterable[str | Path] | None = None,
) -> List[dict]:
    """Scan a local or mounted folder and return file metadata for audits."""

    root = Path(root_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Folder does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a folder: {root}")
    if is_protected_path(root, protected_paths):
        raise ValueError(f"Refusing to scan protected folder: {root}")

    files: List[dict] = []
    count = 0
    cache_hits = 0
    seen_inodes = set()
    cache = {}
    if SMART_SCAN_FOUNDATION and use_cache:
        cache = load_file_cache(str(root), db_path=cache_db_path) if cache_db_path else load_file_cache(str(root))

    print(f"📦 Scanning local folder: {root}")
    for current_root, dirnames, filenames in os.walk(root):
        current_dir = Path(current_root)
        kept_dirnames = []
        for dirname in dirnames:
            child = current_dir / dirname
            relative_dir = child.relative_to(root).as_posix()
            if dirname in DEFAULT_EXCLUDED_DIR_NAMES:
                continue
            if matches_exclusion(relative_dir, dirname, exclude_globs):
                continue
            if is_protected_path(child, protected_paths):
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames
        for filename in filenames:
            path = current_dir / filename
            relative_path = path.relative_to(root)
            relative_id = relative_path.as_posix()
            if matches_exclusion(relative_id, filename, exclude_globs):
                continue
            if is_protected_path(path, protected_paths):
                continue
            try:
                stat = path.stat()
            except OSError as error:
                print(f"⚠️ Skipped unreadable file {path}: {error}")
                continue
            if not path.is_file():
                continue

            parent = relative_path.parent.as_posix() if str(relative_path.parent) != "." else "root"
            blocks_bytes = int(getattr(stat, "st_blocks", 0) or 0) * 512
            if blocks_bytes <= 0:
                blocks_bytes = int(stat.st_size)
            inode_key = (getattr(stat, "st_dev", None), getattr(stat, "st_ino", None))
            hardlink = (
                SMART_SCAN_FOUNDATION
                and inode_key[0] is not None
                and inode_key[1] is not None
                and inode_key in seen_inodes
            )
            if SMART_SCAN_FOUNDATION and inode_key[0] is not None and inode_key[1] is not None:
                seen_inodes.add(inode_key)
            local_file = LocalFile(
                id=relative_id,
                name=path.name,
                path=str(path),
                size_bytes=stat.st_size,
                mimeType=guess_mime_type(path),
                included=not hardlink,
                parents=[parent],
            )
            file_dict = asdict(local_file)
            if SMART_SCAN_FOUNDATION:
                file_dict.update(
                    {
                        "hardlink": hardlink,
                        "blocks_bytes": blocks_bytes,
                        "is_sparse": bool(stat.st_size > 0 and blocks_bytes < stat.st_size * 0.5),
                        "atime": float(stat.st_atime),
                        "mtime": float(stat.st_mtime),
                        "scan_root": str(root),
                    }
                )
                cached = cache.get(relative_id)
                if (
                    cached
                    and float(cached.get("mtime", 0) or 0) == float(stat.st_mtime)
                    and int(cached.get("size_bytes", 0) or 0) == int(stat.st_size)
                    and cached.get("sha256")
                ):
                    file_dict["cached_hash"] = cached["sha256"]
                    cache_hits += 1
            files.append(file_dict)
            count += 1
            if progress_callback:
                progress_callback(
                    {
                        "files_scanned": count,
                        "current_path": str(path),
                        "current_folder": str(current_dir),
                        "cache_hits": cache_hits,
                    }
                )
            if count % 50 == 0:
                print(f"   ...{count} files scanned")

    if not files:
        print("❌ No files found in the selected folder.")
    else:
        print(f"✅ Found {len(files)} files.\n")
    if MEDIA_ANALYSIS:
        _attach_media_probe(files, cache)
    if SMART_SCAN_FOUNDATION and use_cache:
        if cache_db_path:
            save_file_cache(str(root), files, db_path=cache_db_path)
            prune_file_cache(str(root), {file["id"] for file in files}, db_path=cache_db_path)
        else:
            save_file_cache(str(root), files)
            prune_file_cache(str(root), {file["id"] for file in files})
    return files


def estimate_reduction_for_file(
    file: dict,
    max_resolution: tuple[int, int] = HD_RESOLUTION,
    quality: int = DEFAULT_IMAGE_QUALITY,
) -> dict:
    """Estimate non-destructive optimization savings for a file."""

    size_bytes = int(file.get("size_bytes", 0) or 0)
    mime_type = file.get("mimeType") or ""
    if mime_type not in SUPPORTED_IMAGE_MIME_TYPES or size_bytes <= 0:
        return {
            "supported": False,
            "estimated_after_bytes": size_bytes,
            "estimated_saved_bytes": 0,
            "estimated_saved_human": human_readable_size(0),
            "estimated_reduction_percent": 0,
            "reason": "Only common raster image formats can be reduced currently.",
        }

    if mime_type == "image/png":
        base_rate = 0.42
    elif mime_type in {"image/bmp", "image/tiff"}:
        base_rate = 0.58
    elif mime_type == "image/webp":
        base_rate = 0.22
    else:
        base_rate = 0.32

    if size_bytes < 1024 * 1024:
        base_rate *= 0.45
    elif size_bytes > 10 * 1024 * 1024:
        base_rate *= 1.15

    quality_adjustment = max(0.6, min(1.2, (92 - quality) / 18 + 0.75))
    estimated_saved_bytes = int(size_bytes * min(base_rate * quality_adjustment, 0.72))
    target_format = None
    format_conversion_available = IMAGE_EXPANSION and mime_type in {"image/jpeg", "image/png"}
    if format_conversion_available:
        target_format = "webp"
        if mime_type == "image/jpeg":
            webp_after = int((size_bytes - estimated_saved_bytes) * (1 - 0.28))
            estimated_saved_bytes = max(estimated_saved_bytes, size_bytes - webp_after)
    estimated_after_bytes = max(size_bytes - estimated_saved_bytes, 0)

    return {
        "supported": True,
        "estimated_after_bytes": estimated_after_bytes,
        "estimated_saved_bytes": estimated_saved_bytes,
        "estimated_saved_human": human_readable_size(estimated_saved_bytes),
        "estimated_reduction_percent": round((estimated_saved_bytes / size_bytes) * 100, 1),
        "format_conversion_available": format_conversion_available,
        "target_format": target_format,
        "avif_available": AVIF_AVAILABLE,
        "estimated_exif_bytes": 48 * 1024 if mime_type == "image/jpeg" else 0,
        "max_resolution": f"{max_resolution[0]}x{max_resolution[1]}",
        "quality": quality,
        "reason": "Approximation based on file type, current size, target dimensions, and quality.",
    }


def attach_reduction_estimates(
    files: Iterable[dict],
    max_resolution: tuple[int, int] = HD_RESOLUTION,
    quality: int = DEFAULT_IMAGE_QUALITY,
) -> List[dict]:
    """Return files with per-file reduction estimates attached."""

    return [
        {
            **file,
            "reduction": estimate_reduction_for_file(file, max_resolution, quality),
        }
        for file in files
    ]


def attach_duplicate_verification(
    files: Iterable[dict],
    cache_db_path: str | Path | None = None,
) -> List[dict]:
    """Hash duplicate candidates so readable matches can be treated as verified."""

    normalized_files = list(files)
    candidate_groups = {}
    for file in normalized_files:
        size_bytes = int(file.get("size_bytes", 0) or 0)
        if size_bytes <= 0 or file.get("is_sparse") or file.get("included") is False:
            continue
        key = (file.get("name") or "Untitled", size_bytes)
        candidate_groups.setdefault(key, []).append(file)

    candidate_ids = {
        id(file)
        for group in candidate_groups.values()
        if len(group) > 1
        for file in group
    }
    partial_candidates = set()
    if SMART_SCAN_FOUNDATION:
        for group in candidate_groups.values():
            if len(group) <= 1:
                continue
            if any(file.get("cached_hash") for file in group):
                partial_candidates.update(id(file) for file in group)
                continue
            partial_groups = {}
            for file in group:
                try:
                    partial_hash = hash_file_partial(file.get("path") or "")
                except OSError:
                    partial_hash = None
                if partial_hash:
                    partial_groups.setdefault(partial_hash, []).append(file)
            partial_candidates.update(
                id(file)
                for partial_group in partial_groups.values()
                if len(partial_group) > 1
                for file in partial_group
            )

    verified_files = []
    for file in normalized_files:
        if id(file) not in candidate_ids:
            verified_files.append(file)
            continue
        if SMART_SCAN_FOUNDATION and id(file) not in partial_candidates and not file.get("cached_hash"):
            verified_files.append(
                {
                    **file,
                    "duplicate_verification": {
                        "status": "rejected",
                        "algorithm": "partial-sha256",
                    },
                }
            )
            continue

        path = file.get("path") or ""
        try:
            content_hash = file.get("cached_hash") or hash_file_sha256(path)
        except OSError as error:
            verified_files.append(
                {
                    **file,
                    "duplicate_verification": {
                        "status": "unverified",
                        "reason": str(error),
                    },
                }
            )
            continue

        verified_files.append(
            {
                **file,
                "duplicate_verification": {
                    "status": "verified",
                    "algorithm": "sha256",
                    "content_hash": content_hash,
                },
            }
        )
    if SMART_SCAN_FOUNDATION:
        roots = {file.get("scan_root") for file in verified_files if file.get("scan_root")}
        for root in roots:
            root_files = [file for file in verified_files if file.get("scan_root") == root]
            if cache_db_path:
                save_file_cache(str(root), root_files, db_path=cache_db_path)
            else:
                save_file_cache(str(root), root_files)
    return verified_files


def export_to_json_file(data: Iterable[dict], filename: str) -> None:
    """Serialize ``data`` to ``OUTPUT_DIR/filename`` as JSON."""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(OUTPUT_DIR, filename)
    data = list(data)
    if not data:
        print("❌ No data to export.")
        return

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ JSON saved to {filename}")


def file_category(mime_type: str) -> str:
    """Group a MIME type into a storage-audit category."""

    if not mime_type:
        return "other"
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("video/"):
        return "video"
    if mime_type.startswith("audio/"):
        return "audio"
    if mime_type in {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    } or mime_type.startswith("text/"):
        return "document"
    if mime_type in {
        "application/zip",
        "application/x-7z-compressed",
        "application/x-rar-compressed",
        "application/gzip",
        "application/x-tar",
    }:
        return "archive"
    return "other"


def build_storage_audit(files: Iterable[dict], top_n: int = DEFAULT_AUDIT_TOP_N) -> dict:
    """Build a read-only storage audit with cleanup opportunity estimates."""

    normalized_files = []
    for file in files:
        size_bytes = int(file.get("size_bytes", 0) or 0)
        mime_type = file.get("mimeType") or ""
        normalized_files.append(
            {
                **file,
                "name": file.get("name") or "Untitled",
                "path": file.get("path") or "",
                "size_bytes": size_bytes,
                "mimeType": mime_type,
                "category": file_category(mime_type),
                "included": file.get("included", file.get("ownedByMe", True)),
                "parents": file.get("parents") or ["root"],
            }
        )
    for file in normalized_files:
        if file["category"] == "video":
            file["video_estimate"] = estimate_video_savings(file.get("media_probe"))
        elif file["category"] == "audio":
            file["audio_estimate"] = estimate_audio_savings(file.get("media_probe"))

    total_bytes = sum(file["size_bytes"] for file in normalized_files if file.get("included"))
    included_bytes = total_bytes
    hardlink_files = [file for file in normalized_files if file.get("hardlink")]
    sparse_files = [file for file in normalized_files if file.get("is_sparse")]
    sparse_bytes_nominal = sum(file["size_bytes"] for file in sparse_files)

    by_category = {}
    for file in normalized_files:
        category = file["category"]
        category_summary = by_category.setdefault(category, {"count": 0, "bytes": 0})
        category_summary["count"] += 1
        if file.get("included"):
            category_summary["bytes"] += file["size_bytes"]

    by_category = dict(
        sorted(by_category.items(), key=lambda item: item[1]["bytes"], reverse=True)
    )

    by_folder = {}
    for file in normalized_files:
        for parent in file["parents"]:
            folder_summary = by_folder.setdefault(parent, {"count": 0, "bytes": 0})
            folder_summary["count"] += 1
            if file.get("included"):
                folder_summary["bytes"] += file["size_bytes"]

    top_folders = [
        {"folder_id": folder_id, **summary}
        for folder_id, summary in sorted(
            by_folder.items(), key=lambda item: item[1]["bytes"], reverse=True
        )[:top_n]
    ]

    duplicate_groups = {}
    for file in normalized_files:
        if (
            file["size_bytes"] <= 0
            or file.get("included") is False
            or file.get("is_sparse")
        ):
            continue
        key = (file["name"], file["size_bytes"])
        duplicate_groups.setdefault(key, []).append(file)

    duplicate_candidates = []
    duplicate_extra_ids = set()
    duplicate_member_ids = set()
    duplicate_bytes = 0
    duplicate_count = 0

    def add_duplicate_candidate(name: str, size_bytes: int, candidate_set: dict) -> None:
        nonlocal duplicate_bytes, duplicate_count
        candidate_files = candidate_set["files"]
        extra_files = candidate_files[1:]
        recoverable_bytes = sum(file["size_bytes"] for file in extra_files)
        duplicate_member_ids.update(file.get("id") or file.get("path") for file in candidate_files)
        duplicate_extra_ids.update(file.get("id") or file.get("path") for file in extra_files)
        duplicate_count += len(extra_files)
        duplicate_bytes += recoverable_bytes
        duplicate_candidates.append(
            {
                "name": name,
                "size_bytes": size_bytes,
                "copies": len(candidate_files),
                "recoverable_bytes": recoverable_bytes,
                "verification_status": candidate_set["verification_status"],
                "verification_algorithm": candidate_set["verification_algorithm"],
                "confidence": candidate_set["confidence"],
                "files": candidate_files,
            }
        )

    for (name, size_bytes), group in duplicate_groups.items():
        if len(group) <= 1:
            continue

        verified_groups = {}
        unverified_group = []
        for file in group:
            verification = file.get("duplicate_verification") or {}
            content_hash = verification.get("content_hash")
            if verification.get("status") == "verified" and content_hash:
                verified_groups.setdefault(content_hash, []).append(file)
            elif verification.get("status") != "rejected":
                unverified_group.append(file)

        candidate_sets = [
            {
                "files": verified_group,
                "verification_status": "verified",
                "verification_algorithm": "sha256",
                "confidence": "high",
            }
            for verified_group in verified_groups.values()
            if len(verified_group) > 1
        ]
        if not candidate_sets and len(unverified_group) > 1:
            candidate_sets.append(
                {
                    "files": unverified_group,
                    "verification_status": "candidate",
                    "verification_algorithm": None,
                    "confidence": "medium",
                }
            )

        for candidate_set in candidate_sets:
            add_duplicate_candidate(name, size_bytes, candidate_set)

    if SMART_SCAN_FOUNDATION:
        cross_name_groups = {}
        for file in normalized_files:
            file_key = file.get("id") or file.get("path")
            if (
                file["size_bytes"] <= 0
                or file.get("included") is False
                or file.get("is_sparse")
                or file_key in duplicate_member_ids
            ):
                continue
            cross_name_groups.setdefault(file["size_bytes"], []).append(file)

        for size_bytes, group in cross_name_groups.items():
            if len(group) <= 1 or len({file["name"] for file in group}) <= 1:
                continue
            hash_groups = {}
            for file in group:
                verification = file.get("duplicate_verification") or {}
                content_hash = verification.get("content_hash")
                if not content_hash:
                    try:
                        content_hash = file.get("cached_hash") or hash_file_sha256(file.get("path") or "")
                    except OSError:
                        continue
                hash_groups.setdefault(content_hash, []).append(
                    {
                        **file,
                        "duplicate_verification": {
                            "status": "verified",
                            "algorithm": "sha256",
                            "content_hash": content_hash,
                        },
                    }
                )
            for hash_group in hash_groups.values():
                if len(hash_group) <= 1:
                    continue
                add_duplicate_candidate(
                    hash_group[0]["name"],
                    size_bytes,
                    {
                        "files": hash_group,
                        "verification_status": "cross-name",
                        "verification_algorithm": "sha256",
                        "confidence": "high",
                    },
                )

    duplicate_candidates.sort(key=lambda group: group["recoverable_bytes"], reverse=True)

    image_optimization_candidates = [
        file
        for file in normalized_files
        if file["category"] == "image"
        and file["size_bytes"] >= 1024 * 1024
        and file.get("included") is True
        and (file.get("id") or file.get("path")) not in duplicate_extra_ids
    ]
    image_optimization_bytes = int(
        sum(file["size_bytes"] for file in image_optimization_candidates)
        * IMAGE_OPTIMIZATION_SAVINGS_RATE
    )

    large_files = sorted(
        [
            file
            for file in normalized_files
            if file["size_bytes"] >= LARGE_FILE_THRESHOLD_BYTES
        ],
        key=lambda file: file["size_bytes"],
        reverse=True,
    )

    top_files = sorted(normalized_files, key=lambda file: file["size_bytes"], reverse=True)[
        :top_n
    ]
    estimated_recoverable_bytes = duplicate_bytes + image_optimization_bytes
    video_optimization_files = [
        file
        for file in normalized_files
        if (file.get("video_estimate") or {}).get("transcoding_recommended")
    ]
    video_optimization_bytes = sum(
        int((file.get("video_estimate") or {}).get("estimated_hevc_savings_bytes") or 0)
        for file in video_optimization_files
    )
    audio_optimization_files = [
        file
        for file in normalized_files
        if int((file.get("audio_estimate") or {}).get("estimated_opus_savings_bytes") or 0) > 0
    ]
    audio_optimization_bytes = sum(
        int((file.get("audio_estimate") or {}).get("estimated_opus_savings_bytes") or 0)
        for file in audio_optimization_files
    )
    estimated_monthly_cost_avoided = estimate_monthly_storage_cost_usd(
        estimated_recoverable_bytes
    )

    return {
        "summary": {
            "file_count": len(normalized_files),
            "total_bytes": total_bytes,
            "included_count": sum(1 for file in normalized_files if file.get("included")),
            "included_bytes": included_bytes,
            "total_human": human_readable_size(total_bytes),
            "included_human": human_readable_size(included_bytes),
            "hardlink_count": len(hardlink_files),
            "hardlink_bytes_saved": sum(file["size_bytes"] for file in hardlink_files),
            "sparse_file_count": len(sparse_files),
            "sparse_bytes_nominal": sparse_bytes_nominal,
        },
        "by_category": by_category,
        "top_files": top_files,
        "top_folders": top_folders,
        "duplicate_candidates": duplicate_candidates[:top_n],
        "large_files": large_files[:top_n],
        "opportunities": {
            "duplicate_count": duplicate_count,
            "duplicate_bytes": duplicate_bytes,
            "duplicate_human": human_readable_size(duplicate_bytes),
            "image_optimization_count": len(image_optimization_candidates),
            "image_optimization_bytes": image_optimization_bytes,
            "image_optimization_human": human_readable_size(image_optimization_bytes),
            "large_file_count": len(large_files),
            "large_file_bytes": sum(file["size_bytes"] for file in large_files),
            "large_file_human": human_readable_size(
                sum(file["size_bytes"] for file in large_files)
            ),
            "video_optimization_count": len(video_optimization_files),
            "video_optimization_bytes": video_optimization_bytes,
            "video_optimization_human": human_readable_size(video_optimization_bytes),
            "audio_optimization_count": len(audio_optimization_files),
            "audio_optimization_bytes": audio_optimization_bytes,
            "audio_optimization_human": human_readable_size(audio_optimization_bytes),
            "estimated_recoverable_bytes": estimated_recoverable_bytes,
            "estimated_recoverable_human": human_readable_size(
                estimated_recoverable_bytes
            ),
            "estimated_monthly_cost_avoided_usd": estimated_monthly_cost_avoided,
            "estimated_monthly_cost_avoided_human": f"${estimated_monthly_cost_avoided:.2f}/mo",
            "cost_estimate_rate_usd_per_gb_month": CLOUD_STORAGE_COST_PER_GB_MONTH_USD,
        },
    }


def _render_metric(label: str, value: str) -> str:
    return f"<div class='metric'><span>{escape(label)}</span><strong>{escape(value)}</strong></div>"


def _render_file_rows(files: Iterable[dict]) -> str:
    rows = []
    for file in files:
        name = escape(file["name"])
        path = escape(file.get("path", ""))
        link = f"<a href='{path}'>{name}</a>" if path else name
        rows.append(
            "<tr>"
            f"<td>{link}</td>"
            f"<td>{escape(file.get('category', 'other'))}</td>"
            f"<td>{escape(human_readable_size(file['size_bytes']))}</td>"
            "</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan='3'>No matching files</td></tr>"


def render_storage_audit_html(audit: dict) -> str:
    """Render an HTML dashboard for a storage audit."""

    category_rows = "\n".join(
        "<tr>"
        f"<td>{escape(category)}</td>"
        f"<td>{summary['count']}</td>"
        f"<td>{escape(human_readable_size(summary['bytes']))}</td>"
        "</tr>"
        for category, summary in audit["by_category"].items()
    )
    folder_rows = "\n".join(
        "<tr>"
        f"<td>{escape(folder['folder_id'])}</td>"
        f"<td>{folder['count']}</td>"
        f"<td>{escape(human_readable_size(folder['bytes']))}</td>"
        "</tr>"
        for folder in audit["top_folders"]
    )
    duplicate_rows = "\n".join(
        "<tr>"
        f"<td>{escape(group['name'])}</td>"
        f"<td>{group['copies']}</td>"
        f"<td>{escape(human_readable_size(group['recoverable_bytes']))}</td>"
        "</tr>"
        for group in audit["duplicate_candidates"]
    )

    summary = audit["summary"]
    opportunities = audit["opportunities"]
    metrics = "\n".join(
        [
            _render_metric("Files scanned", str(summary["file_count"])),
            _render_metric("Total storage", summary["total_human"]),
            _render_metric("Included storage", summary["included_human"]),
            _render_metric("Estimated recoverable", opportunities["estimated_recoverable_human"]),
            _render_metric("Duplicate candidates", opportunities["duplicate_human"]),
            _render_metric("Image optimization", opportunities["image_optimization_human"]),
        ]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CloudSaver Storage Audit</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #172026; background: #f5f7f9; }}
    header {{ background: #172026; color: white; padding: 28px 32px; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 24px; }}
    h1, h2 {{ margin: 0; }}
    h2 {{ margin-top: 28px; margin-bottom: 12px; font-size: 20px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 20px; }}
    .metric {{ background: white; border: 1px solid #d8dee4; border-radius: 8px; padding: 16px; }}
    .metric span {{ display: block; color: #52606d; font-size: 13px; margin-bottom: 8px; }}
    .metric strong {{ font-size: 22px; }}
    section {{ background: white; border: 1px solid #d8dee4; border-radius: 8px; padding: 18px; margin-top: 18px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 10px; border-bottom: 1px solid #e6e9ed; text-align: left; }}
    th {{ color: #52606d; font-size: 12px; text-transform: uppercase; }}
    a {{ color: #1267b2; }}
  </style>
</head>
<body>
  <header>
    <h1>CloudSaver Storage Audit</h1>
    <p>Read-only scan with cleanup opportunities and storage concentration.</p>
  </header>
  <main>
    <div class="metrics">{metrics}</div>
    <section>
      <h2>Storage By Category</h2>
      <table><thead><tr><th>Category</th><th>Files</th><th>Storage</th></tr></thead><tbody>{category_rows}</tbody></table>
    </section>
    <section>
      <h2>Largest Files</h2>
      <table><thead><tr><th>File</th><th>Category</th><th>Size</th></tr></thead><tbody>{_render_file_rows(audit["top_files"])}</tbody></table>
    </section>
    <section>
      <h2>Largest Folders</h2>
      <table><thead><tr><th>Folder</th><th>Files</th><th>Storage</th></tr></thead><tbody>{folder_rows}</tbody></table>
    </section>
    <section>
      <h2>Duplicate Candidates</h2>
      <table><thead><tr><th>Name</th><th>Copies</th><th>Recoverable</th></tr></thead><tbody>{duplicate_rows or "<tr><td colspan='3'>No duplicate candidates</td></tr>"}</tbody></table>
    </section>
    <section>
      <h2>Large Files To Review</h2>
      <table><thead><tr><th>File</th><th>Category</th><th>Size</th></tr></thead><tbody>{_render_file_rows(audit["large_files"])}</tbody></table>
    </section>
  </main>
</body>
</html>
"""


def export_storage_audit_dashboard(files: Iterable[dict]) -> dict:
    """Generate JSON and HTML storage audit artifacts in ``OUTPUT_DIR``."""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    audit = build_storage_audit(files)
    json_path = os.path.join(OUTPUT_DIR, "storage_audit.json")
    html_path = os.path.join(OUTPUT_DIR, "storage_audit.html")

    with open(json_path, "w") as f:
        json.dump(audit, f, indent=2)

    with open(html_path, "w") as f:
        f.write(render_storage_audit_html(audit))

    print("✅ Storage audit generated.")
    print(f"   JSON: {json_path}")
    print(f"   Dashboard: {html_path}")
    print(
        "💾 Estimated recoverable space: "
        f"{audit['opportunities']['estimated_recoverable_human']}"
    )
    return audit


def reduce_image_to_1080p(input_path: str, output_path: str) -> tuple[int, int]:
    """Reduce ``input_path`` to ``HD_RESOLUTION`` and write the result."""

    before_size = os.path.getsize(input_path)
    with Image.open(input_path) as img:
        img.thumbnail(HD_RESOLUTION, Image.LANCZOS)
        img.save(output_path)

    after_size = os.path.getsize(output_path)
    print(f"🖼️ Reduced: {os.path.basename(input_path)}")
    print(f"   Path: {output_path}")
    print(f"   Size before: {human_readable_size(before_size)}")
    print(f"   Size after:  {human_readable_size(after_size)}")
    return before_size, after_size


def reduce_image_copy(
    input_path: str,
    output_path: str,
    max_resolution: tuple[int, int] = HD_RESOLUTION,
    quality: int = DEFAULT_IMAGE_QUALITY,
    target_format: str | None = None,
) -> tuple[int, int]:
    """Create a reduced image copy without modifying the original file."""

    result = _write_image_copy(input_path, output_path, max_resolution, quality, target_format)
    return result["before_bytes"], result["after_bytes"]


def _write_image_copy(
    input_path: str,
    output_path: str,
    max_resolution: tuple[int, int] = HD_RESOLUTION,
    quality: int = DEFAULT_IMAGE_QUALITY,
    target_format: str | None = None,
) -> dict:
    """Write an optimized image copy and return detailed size metadata."""

    before_size = os.path.getsize(input_path)
    with Image.open(input_path) as img:
        original_format = img.format
        img.thumbnail(max_resolution, Image.LANCZOS)
        output_format = (target_format or original_format or "").upper()
        if output_format == "JPG":
            output_format = "JPEG"
        if output_format == "AVIF" and not AVIF_AVAILABLE:
            raise RuntimeError("AVIF conversion is not available.")
        save_kwargs = {}
        if output_format in {"JPEG", "PNG", "WEBP", "AVIF"}:
            save_kwargs["optimize"] = True
        if output_format in {"JPEG", "WEBP", "AVIF"}:
            save_kwargs["quality"] = quality
        if img.mode in {"RGBA", "P"} and output_format == "JPEG":
            img = img.convert("RGB")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if output_format:
            save_kwargs["format"] = output_format
        img.save(output_path, **save_kwargs)

    exif_bytes_stripped = 0
    if PIEXIF_AVAILABLE and (target_format or original_format or "").upper() in {"JPEG", "JPG"}:
        before_strip = os.path.getsize(output_path)
        try:
            piexif.remove(output_path)
            exif_bytes_stripped = max(before_strip - os.path.getsize(output_path), 0)
        except Exception:
            exif_bytes_stripped = 0

    after_size = os.path.getsize(output_path)
    return {
        "before_bytes": before_size,
        "after_bytes": after_size,
        "exif_bytes_stripped": exif_bytes_stripped,
    }


def converted_image_output_path(output_dir: str | Path, file_id: str, target_format: str) -> Path:
    output_path = Path(output_dir) / file_id
    return output_path.with_suffix(f".{target_format.lower()}")


def reduce_selected_images(
    root_path: str,
    file_ids: Iterable[str],
    output_dir: str = REDUCED_DIR,
    max_resolution: tuple[int, int] = HD_RESOLUTION,
    quality: int = DEFAULT_IMAGE_QUALITY,
) -> dict:
    """Reduce selected local images into ``output_dir`` while preserving relative paths."""

    root = Path(root_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise NotADirectoryError(f"Path is not a folder: {root}")

    results = []
    total_before = 0
    total_after = 0
    for file_id in file_ids:
        source_path = (root / file_id).resolve()
        if not is_path_within(source_path, root):
            results.append({"id": file_id, "status": "skipped", "error": "Path is outside scan root."})
            continue
        if not source_path.exists() or not source_path.is_file():
            results.append({"id": file_id, "status": "skipped", "error": "File no longer exists."})
            continue

        mime_type = guess_mime_type(source_path)
        if mime_type not in SUPPORTED_IMAGE_MIME_TYPES:
            results.append(
                {"id": file_id, "status": "skipped", "error": "File type cannot be reduced."}
            )
            continue

        output_path = Path(output_dir) / file_id
        try:
            before_size, after_size = reduce_image_copy(
                str(source_path), str(output_path), max_resolution, quality
            )
        except Exception as error:
            results.append({"id": file_id, "status": "failed", "error": str(error)})
            continue

        saved_bytes = max(before_size - after_size, 0)
        total_before += before_size
        total_after += after_size
        results.append(
            {
                "id": file_id,
                "status": "reduced",
                "source_path": str(source_path),
                "output_path": str(output_path),
                "before_bytes": before_size,
                "after_bytes": after_size,
                "saved_bytes": saved_bytes,
                "saved_human": human_readable_size(saved_bytes),
            }
        )

    total_saved = max(total_before - total_after, 0)
    return {
        "results": results,
        "total_before_bytes": total_before,
        "total_after_bytes": total_after,
        "total_saved_bytes": total_saved,
        "total_saved_human": human_readable_size(total_saved),
    }


def convert_image_format(
    root_path: str,
    file_ids: Iterable[str],
    target_format: str,
    output_dir: str = REDUCED_DIR,
    max_resolution: tuple[int, int] = HD_RESOLUTION,
    quality: int = DEFAULT_IMAGE_QUALITY,
) -> dict:
    """Convert selected image files into a new format without changing originals."""

    target_format = (target_format or "").lower()
    if target_format not in {"webp", "avif"}:
        raise ValueError("Target format must be webp or avif.")
    if target_format == "avif" and not AVIF_AVAILABLE:
        raise RuntimeError("AVIF conversion is not available.")

    root = Path(root_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise NotADirectoryError(f"Path is not a folder: {root}")

    results = []
    total_before = 0
    total_after = 0
    for file_id in file_ids:
        source_path = (root / file_id).resolve()
        if not is_path_within(source_path, root):
            results.append({"id": file_id, "status": "skipped", "error": "Path is outside scan root."})
            continue
        if not source_path.exists() or not source_path.is_file():
            results.append({"id": file_id, "status": "skipped", "error": "File no longer exists."})
            continue
        mime_type = guess_mime_type(source_path)
        if mime_type not in SUPPORTED_IMAGE_MIME_TYPES:
            results.append(
                {"id": file_id, "status": "skipped", "error": "File type cannot be converted."}
            )
            continue

        output_path = converted_image_output_path(output_dir, file_id, target_format)
        try:
            details = _write_image_copy(
                str(source_path),
                str(output_path),
                max_resolution,
                quality,
                target_format,
            )
        except Exception as error:
            results.append({"id": file_id, "status": "failed", "error": str(error)})
            continue

        before_size = details["before_bytes"]
        after_size = details["after_bytes"]
        saved_bytes = max(before_size - after_size, 0)
        total_before += before_size
        total_after += after_size
        results.append(
            {
                "id": file_id,
                "status": "reduced",
                "source_path": str(source_path),
                "output_path": str(output_path),
                "before_bytes": before_size,
                "after_bytes": after_size,
                "saved_bytes": saved_bytes,
                "saved_human": human_readable_size(saved_bytes),
                "target_format": target_format,
                "exif_bytes_stripped": details["exif_bytes_stripped"],
            }
        )

    total_saved = max(total_before - total_after, 0)
    return {
        "results": results,
        "total_before_bytes": total_before,
        "total_after_bytes": total_after,
        "total_saved_bytes": total_saved,
        "total_saved_human": human_readable_size(total_saved),
    }


def optimize_png_lossless(path: str | Path) -> tuple[int, int]:
    """Run oxipng lossless optimization on a PNG path when available."""

    if not OXIPNG_AVAILABLE:
        raise RuntimeError("oxipng not available")
    path = Path(path).expanduser().resolve()
    before_size = path.stat().st_size
    subprocess.run(
        ["oxipng", "-o", "4", "--strip", "safe", "--quiet", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return before_size, path.stat().st_size


def compute_perceptual_hashes(files: Iterable[dict]) -> list[dict]:
    """Compute perceptual image hashes when the optional imagehash dependency exists."""

    if not PERCEPTUAL_HASH_AVAILABLE:
        return []
    hashes = []
    for file in files:
        if file.get("category") != "image" or int(file.get("size_bytes", 0) or 0) < 102400:
            continue
        try:
            with _PilImage.open(file.get("path") or "") as img:
                hashes.append({"id": file.get("id"), "phash": str(imagehash.phash(img))})
        except Exception:
            continue
    return hashes


def _phash_distance(first: str, second: str) -> int:
    try:
        return bin(int(first, 16) ^ int(second, 16)).count("1")
    except ValueError:
        return 64


def find_perceptual_duplicates(files: Iterable[dict], threshold: int = 10) -> list[dict]:
    """Find visually similar image groups using pHash Hamming distance."""

    normalized_files = [
        {**file, "category": file.get("category") or file_category(file.get("mimeType") or "")}
        for file in files
        if (file.get("category") or file_category(file.get("mimeType") or "")) == "image"
    ]
    if len(normalized_files) >= 5000:
        return []
    phashes = compute_perceptual_hashes(normalized_files)
    by_id = {file.get("id"): file for file in normalized_files}
    seen = set()
    groups = []
    for item in phashes:
        if item["id"] in seen:
            continue
        group = [by_id[item["id"]]]
        for other in phashes:
            if other["id"] == item["id"] or other["id"] in seen:
                continue
            if _phash_distance(item["phash"], other["phash"]) <= threshold:
                group.append(by_id[other["id"]])
        if len(group) > 1:
            seen.update(file.get("id") for file in group)
            recoverable_bytes = sum(file.get("size_bytes", 0) for file in group[1:])
            groups.append(
                {
                    "name": group[0].get("name") or "Similar images",
                    "size_bytes": group[0].get("size_bytes", 0),
                    "copies": len(group),
                    "recoverable_bytes": recoverable_bytes,
                    "verification_status": "perceptual",
                    "verification_algorithm": "phash",
                    "confidence": "medium",
                    "files": group,
                }
            )
    return sorted(groups, key=lambda group: group["recoverable_bytes"], reverse=True)


def quarantine_selected_files(
    root_path: str,
    file_ids: Iterable[str],
    quarantine_dir: str | None = None,
    protected_paths: Iterable[str | Path] | None = None,
) -> dict:
    """Move selected files to a review folder with a restore manifest."""

    root = Path(root_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise NotADirectoryError(f"Path is not a folder: {root}")

    review_root = Path(quarantine_dir).expanduser().resolve() if quarantine_dir else root / QUARANTINE_DIR_NAME
    batch_dir = review_root / time.strftime("%Y%m%d-%H%M%S")
    batch_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for file_id in file_ids:
        source_path = (root / file_id).resolve()
        if not is_path_within(source_path, root):
            results.append({"id": file_id, "status": "skipped", "error": "Path is outside scan root."})
            continue
        if not source_path.exists() or not source_path.is_file():
            results.append({"id": file_id, "status": "skipped", "error": "File no longer exists."})
            continue
        if is_protected_path(source_path, protected_paths):
            results.append({"id": file_id, "status": "skipped", "error": "File is in a protected folder."})
            continue
        if is_path_within(source_path, review_root):
            results.append({"id": file_id, "status": "skipped", "error": "File is already in review."})
            continue

        destination_path = batch_dir / file_id
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(destination_path))
        results.append(
            {
                "id": file_id,
                "status": "quarantined",
                "source_path": str(source_path),
                "review_path": str(destination_path),
            }
        )

    manifest = {
        "root_path": str(root),
        "created_at": time.time(),
        "results": results,
    }
    manifest_path = batch_dir / "manifest.json"
    with open(manifest_path, "w") as file:
        json.dump(manifest, file, indent=2)

    return {
        "review_dir": str(batch_dir),
        "manifest_path": str(manifest_path),
        "results": results,
        "quarantined_count": sum(1 for result in results if result["status"] == "quarantined"),
    }


def restore_quarantine(manifest_path: str) -> dict:
    """Restore files moved by ``quarantine_selected_files``."""

    manifest_file = Path(manifest_path).expanduser().resolve()
    with open(manifest_file) as file:
        manifest = json.load(file)

    results = []
    for item in manifest.get("results", []):
        if item.get("status") != "quarantined":
            continue
        source = Path(item["review_path"])
        destination = Path(item["source_path"])
        if not source.exists():
            results.append({"id": item["id"], "status": "skipped", "error": "Review file missing."})
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        results.append({"id": item["id"], "status": "restored", "source_path": str(destination)})

    return {"manifest_path": str(manifest_file), "results": results}


def export_large_files(files: Iterable[dict], threshold_mb: float) -> None:
    """Export local files larger than ``threshold_mb`` to JSON."""

    threshold_bytes = threshold_mb * 1024 * 1024
    large_files = [file for file in files if file["size_bytes"] > threshold_bytes]
    if not large_files:
        print("❌ No files found above the specified size.")
        return
    export_to_json_file(large_files, f"files_above_{int(threshold_mb)}MB.json")


def reduce_local_images(files: Iterable[dict], min_size_mb: float, number_of_files: int) -> None:
    """Create reduced copies of local images in ``REDUCED_DIR``."""

    os.makedirs(REDUCED_DIR, exist_ok=True)
    min_size_bytes = min_size_mb * 1024 * 1024
    image_files = [
        file
        for file in files
        if file.get("mimeType", "").startswith("image/")
        and file.get("size_bytes", 0) > min_size_bytes
    ]
    if not image_files:
        print("❌ No image files found above the specified size.")
        return

    total_bytes_saved = 0
    for file in image_files[:number_of_files]:
        source_path = file["path"]
        relative_id = file.get("id") or file["name"]
        output_path = os.path.join(REDUCED_DIR, relative_id)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            before, after = reduce_image_copy(source_path, output_path)
            total_bytes_saved += max(before - after, 0)
        except Exception as error:
            print(f"⚠️ Skipped image {source_path}: {error}")

    print(f"\n💾 Estimated space saved by reduced copies: {human_readable_size(total_bytes_saved)}")


def find_duplicates(files: Iterable[dict]) -> dict:
    """Find duplicate candidates by name and size without deleting anything."""

    audit = build_storage_audit(files)
    opportunities = audit["opportunities"]
    duplicates = audit["duplicate_candidates"]
    if not duplicates:
        print("✅ No duplicate candidates found.")
        return audit

    print(f"⚠️ Found {opportunities['duplicate_count']} duplicate candidate files.")
    print(f"💾 Estimated recoverable space: {opportunities['duplicate_human']}")
    for group in duplicates:
        print(
            f"   {group['name']} - {group['copies']} copies, "
            f"{human_readable_size(group['recoverable_bytes'])} recoverable"
        )
    print("ℹ️ No files were deleted. Review the storage audit before removing files.")
    return audit


def prompt_for_folder() -> str:
    return input("📁 Enter local or mounted folder path: ").strip()


def main():
    parser = argparse.ArgumentParser(description="Run the CloudSaver local storage CLI.")
    parser.add_argument("folder", nargs="?", help="Local or mounted folder path to scan.")
    args = parser.parse_args()

    print("💾 CloudSaver local storage optimizer")
    folder_path = args.folder or prompt_for_folder()
    try:
        scanned_files = scan_local_folder(folder_path)
    except (FileNotFoundError, NotADirectoryError) as error:
        print(f"❌ {error}")
        return

    while True:
        print("\n🎮 Choose an option:")
        print("1. Run storage audit dashboard")
        print("2. Export all file info to JSON")
        print("3. Export only files larger than X MB to JSON")
        print("4. Create reduced copies of first X images above X MB")
        print("5. Find duplicate candidates by name and size")
        print("6. Rescan folder")
        print("7. Exit")

        choice = input("👉 Enter choice [1-7]: ").strip()

        if choice == "1":
            export_storage_audit_dashboard(scanned_files)

        elif choice == "2":
            export_to_json_file(scanned_files, "all_files.json")

        elif choice == "3":
            threshold_str = input("📏 Enter minimum file size in MB: ").strip()
            try:
                export_large_files(scanned_files, float(threshold_str))
            except ValueError:
                print("❌ Invalid number entered.")

        elif choice == "4":
            try:
                number_of_files = int(
                    input("🔢 Enter the number of files you want to compress: ").strip()
                )
                threshold_mb = float(input("📏 Enter minimum image file size in MB: ").strip())
                reduce_local_images(scanned_files, threshold_mb, number_of_files)
            except ValueError:
                print("❌ Invalid number entered.")

        elif choice == "5":
            find_duplicates(scanned_files)

        elif choice == "6":
            folder_path = prompt_for_folder()
            try:
                scanned_files = scan_local_folder(folder_path)
            except (FileNotFoundError, NotADirectoryError) as error:
                print(f"❌ {error}")

        elif choice == "7":
            print("👋 Exiting.")
            break

        else:
            print("❌ Invalid choice. Try again.")


if __name__ == "__main__":
    main()
