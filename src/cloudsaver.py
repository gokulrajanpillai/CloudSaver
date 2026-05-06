import json
import mimetypes
import os
from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path
from typing import Iterable, List

from PIL import Image


OUTPUT_DIR = "output"
REDUCED_DIR = os.path.join(OUTPUT_DIR, "reduced")

HD_RESOLUTION = (1920, 1080)
DEFAULT_AUDIT_TOP_N = 10
LARGE_FILE_THRESHOLD_BYTES = 100 * 1024 * 1024
IMAGE_OPTIMIZATION_SAVINGS_RATE = 0.35
SUPPORTED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
}
DEFAULT_IMAGE_QUALITY = 82


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


def is_path_within(child_path: Path, parent_path: Path) -> bool:
    """Return whether ``child_path`` is inside ``parent_path`` after resolving both."""

    try:
        child_path.resolve().relative_to(parent_path.resolve())
        return True
    except ValueError:
        return False


def guess_mime_type(path: Path) -> str:
    """Infer a MIME type from a local file path."""

    mime_type, _ = mimetypes.guess_type(path)
    return mime_type or "application/octet-stream"


def scan_local_folder(root_path: str) -> List[dict]:
    """Scan a local or mounted folder and return file metadata for audits."""

    root = Path(root_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Folder does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a folder: {root}")

    files: List[dict] = []
    count = 0
    print(f"📦 Scanning local folder: {root}")
    for current_root, _, filenames in os.walk(root):
        current_dir = Path(current_root)
        for filename in filenames:
            path = current_dir / filename
            try:
                stat = path.stat()
            except OSError as error:
                print(f"⚠️ Skipped unreadable file {path}: {error}")
                continue
            if not path.is_file():
                continue

            relative_path = path.relative_to(root)
            parent = str(relative_path.parent) if str(relative_path.parent) != "." else "root"
            local_file = LocalFile(
                id=str(relative_path),
                name=path.name,
                path=str(path),
                size_bytes=stat.st_size,
                mimeType=guess_mime_type(path),
                included=True,
                parents=[parent],
            )
            files.append(asdict(local_file))
            count += 1
            if count % 50 == 0:
                print(f"   ...{count} files scanned")

    if not files:
        print("❌ No files found in the selected folder.")
    else:
        print(f"✅ Found {len(files)} files.\n")
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
    estimated_after_bytes = max(size_bytes - estimated_saved_bytes, 0)

    return {
        "supported": True,
        "estimated_after_bytes": estimated_after_bytes,
        "estimated_saved_bytes": estimated_saved_bytes,
        "estimated_saved_human": human_readable_size(estimated_saved_bytes),
        "estimated_reduction_percent": round((estimated_saved_bytes / size_bytes) * 100, 1),
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

    total_bytes = sum(file["size_bytes"] for file in normalized_files)
    included_bytes = sum(file["size_bytes"] for file in normalized_files if file.get("included"))

    by_category = {}
    for file in normalized_files:
        category = file["category"]
        category_summary = by_category.setdefault(category, {"count": 0, "bytes": 0})
        category_summary["count"] += 1
        category_summary["bytes"] += file["size_bytes"]

    by_category = dict(
        sorted(by_category.items(), key=lambda item: item[1]["bytes"], reverse=True)
    )

    by_folder = {}
    for file in normalized_files:
        for parent in file["parents"]:
            folder_summary = by_folder.setdefault(parent, {"count": 0, "bytes": 0})
            folder_summary["count"] += 1
            folder_summary["bytes"] += file["size_bytes"]

    top_folders = [
        {"folder_id": folder_id, **summary}
        for folder_id, summary in sorted(
            by_folder.items(), key=lambda item: item[1]["bytes"], reverse=True
        )[:top_n]
    ]

    duplicate_groups = {}
    for file in normalized_files:
        if file["size_bytes"] <= 0:
            continue
        key = (file["name"], file["size_bytes"])
        duplicate_groups.setdefault(key, []).append(file)

    duplicate_candidates = []
    duplicate_extra_ids = set()
    duplicate_bytes = 0
    duplicate_count = 0
    for (name, size_bytes), group in duplicate_groups.items():
        if len(group) <= 1:
            continue
        extra_files = group[1:]
        duplicate_extra_ids.update(file.get("id") or file.get("path") for file in extra_files)
        duplicate_count += len(extra_files)
        duplicate_bytes += sum(file["size_bytes"] for file in extra_files)
        duplicate_candidates.append(
            {
                "name": name,
                "size_bytes": size_bytes,
                "copies": len(group),
                "recoverable_bytes": sum(file["size_bytes"] for file in extra_files),
                "files": group,
            }
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

    return {
        "summary": {
            "file_count": len(normalized_files),
            "total_bytes": total_bytes,
            "included_bytes": included_bytes,
            "total_human": human_readable_size(total_bytes),
            "included_human": human_readable_size(included_bytes),
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
            "estimated_recoverable_bytes": duplicate_bytes + image_optimization_bytes,
            "estimated_recoverable_human": human_readable_size(
                duplicate_bytes + image_optimization_bytes
            ),
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
) -> tuple[int, int]:
    """Create a reduced image copy without modifying the original file."""

    before_size = os.path.getsize(input_path)
    with Image.open(input_path) as img:
        original_format = img.format
        img.thumbnail(max_resolution, Image.LANCZOS)
        save_kwargs = {}
        if original_format in {"JPEG", "PNG", "WEBP"}:
            save_kwargs["optimize"] = True
        if original_format in {"JPEG", "WEBP"}:
            save_kwargs["quality"] = quality
        if img.mode in {"RGBA", "P"} and original_format == "JPEG":
            img = img.convert("RGB")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, **save_kwargs)

    after_size = os.path.getsize(output_path)
    return before_size, after_size


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
    print("💾 CloudSaver local storage optimizer")
    folder_path = prompt_for_folder()
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
