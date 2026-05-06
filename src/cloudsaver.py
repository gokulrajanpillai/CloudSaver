import os
import json
import io
from dataclasses import asdict, dataclass
from html import escape
from typing import Iterable, List

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from PIL import Image

# SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
SCOPES = ["https://www.googleapis.com/auth/drive"]

MEDIA_QUERY = "mimeType contains 'image/' or mimeType contains 'video/'"
LIST_FIELDS = "nextPageToken, files(id, name, mimeType, size, ownedByMe, parents)"

OUTPUT_DIR = "output"
DOWNLOAD_DIR = os.path.join(OUTPUT_DIR, "downloaded")
REDUCED_DIR = os.path.join(OUTPUT_DIR, "reduced")

QUERY_MEDIA_FILES = "(mimeType contains 'image/' or mimeType contains 'video/') and 'me' in owners and trashed = false"
QUERY_ALL_FILES = "'me' in owners and trashed = false"
HD_RESOLUTION = (1920, 1080)
DEFAULT_AUDIT_TOP_N = 10
LARGE_FILE_THRESHOLD_BYTES = 100 * 1024 * 1024
IMAGE_OPTIMIZATION_SAVINGS_RATE = 0.35


@dataclass
class MediaFile:
    """Simplified representation of a Google Drive media file."""

    id: str
    name: str
    path: str
    size_bytes: int
    mimeType: str
    ownedByMe: bool
    parents: List[str]


def human_readable_size(size_bytes: int) -> str:
    """Convert byte counts into a human-readable string."""

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def regenerate_token_and_credentials():
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    os.remove("token.json") if os.path.exists("token.json") else None
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())
        print("🔑 Token regenerated and saved to token.json")
    return creds


def authenticate() -> object:
    """Authenticate using OAuth and return a Drive service client."""

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid or creds.expired:
            creds = regenerate_token_and_credentials()
    else:
        creds = regenerate_token_and_credentials()
    return build('drive', 'v3', credentials=creds)


def fetch_files(service, query) -> List[dict]:
    """Retrieve metadata for all image and video files in Drive."""

    page_token = None
    all_files: List[dict] = []
    count = 0

    print("📦 Scanning Drive for media files (this may take a while)...")
    while True:
        response = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields=LIST_FIELDS,
                pageToken=page_token,
            )
            .execute()
        )

        for file in response.get("files", []):
            media = MediaFile(
                id=file.get("id"),
                name=file.get("name"),
                path=f"https://drive.google.com/file/d/{file.get('id')}/view",
                size_bytes=int(file.get("size", 0)),
                mimeType=file.get("mimeType"),
                ownedByMe=file.get("ownedByMe"),
                parents=file.get("parents", []),
            )
            all_files.append(asdict(media))
            count += 1
            if count % 50 == 0:
                print(f"   ...{count} files scanned")

        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    if not all_files:
        print("❌ No files matching the query found in Google Drive.")
    else:
        print(f"✅ Found {len(all_files)} files matching the query.\n")
    return all_files


def export_to_json_file(data: Iterable[dict], filename: str) -> None:
    """Serialize ``data`` to ``OUTPUT_DIR/filename`` as JSON."""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(OUTPUT_DIR, filename)
    if not data:
        print("❌ No data to export.")
        return

    with open(filename, "w") as f:
        json.dump(list(data), f, indent=2)

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
    if mime_type == "application/vnd.google-apps.folder":
        return "folder"
    if mime_type.startswith("application/vnd.google-apps."):
        return "google_workspace"
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
                "parents": file.get("parents") or ["root"],
            }
        )

    total_bytes = sum(file["size_bytes"] for file in normalized_files)
    owned_bytes = sum(file["size_bytes"] for file in normalized_files if file.get("ownedByMe"))

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
        and file.get("ownedByMe") is True
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
            "owned_bytes": owned_bytes,
            "total_human": human_readable_size(total_bytes),
            "owned_human": human_readable_size(owned_bytes),
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
            _render_metric("Owned storage", summary["owned_human"]),
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
      <table><thead><tr><th>Folder ID</th><th>Files</th><th>Storage</th></tr></thead><tbody>{folder_rows}</tbody></table>
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


def download_and_reduce_images(
    service: object, files: Iterable[dict], min_size_mb: float, number_of_files: int
) -> None:
    """Download and compress images meeting ``min_size_mb``."""

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(REDUCED_DIR, exist_ok=True)
    total_bytes_saved = 0
    min_size_bytes = min_size_mb * 1024 * 1024
    image_files = [
        f
        for f in files
        if f.get("mimeType", "").startswith("image/")
        and f.get("size_bytes", 0) > min_size_bytes
        and f.get("ownedByMe") is True
    ]
    if not image_files:
        print("❌ No image files found above the specified size.")
        return
    selected_files = image_files[:number_of_files]
    reduced_paths = []
    for file in selected_files:
        print(f"⬇️ Downloading {file['name']} ({human_readable_size(file['size_bytes'])})")
        print(f"   Google Drive Path: {file['path']}")
        request = service.files().get_media(fileId=file['path'].split('/')[-2])
        fh = io.BytesIO()
        try:
            from googleapiclient.http import MediaIoBaseDownload

            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            fh.seek(0)
            local_path = os.path.join(DOWNLOAD_DIR, file['name'])
            with open(local_path, 'wb') as out_file:
                out_file.write(fh.read())
            print(f"✅ Saved to {local_path}")
            reduced_path = os.path.join(REDUCED_DIR, file['name'])
            try:
                before, after = reduce_image_to_1080p(local_path, reduced_path)
                total_bytes_saved += before - after
                reduced_paths.append((file, reduced_path))
            except Exception as img_err:
                print(f"⚠️ Skipped corrupted image {file['name']}: {img_err}")
                continue
        except Exception as e:
            print(f"❌ Failed to download/reduce {file['name']}: {e}")

    # Optionally ask user to replace files in Google Drive
    if reduced_paths:
        print(
            f"\n💾 After replacement you will have saved: {human_readable_size(total_bytes_saved)}"
        )
        answer = (
            input(
                "❓ Do you want to replace the original files in Google Drive with their reduced versions? [y/N]: "
            )
            .strip()
            .lower()
        )
        if answer == "y":
            for file, reduced_path in reduced_paths:
                try:
                    file_id = file['path'].split('/')[-2]
                    # Move original file to trash
                    service.files().update(fileId=file_id, body={'trashed': True}).execute()
                    print(f"🗑️ Moved original {file['name']} to trash in Google Drive.")
                    # Upload reduced file as a new file
                    from googleapiclient.http import MediaFileUpload

                    media_body = MediaFileUpload(
                        reduced_path, mimetype=file['mimeType'], resumable=True
                    )
                    new_file_metadata = {'name': file['name'], 'mimeType': file['mimeType']}
                    new_file = (
                        service.files()
                        .create(body=new_file_metadata, media_body=media_body)
                        .execute()
                    )
                    print(f"🔄 Uploaded reduced version of {file['name']} to Google Drive.")
                except Exception as e:
                    print(f"❌ Failed to replace {file['name']} in Google Drive: {e}")
        print(f"\n💾 Total space saved: {human_readable_size(total_bytes_saved)}")


def find_duplicates(service, files):
    from collections import defaultdict

    print("🔍 Scanning for duplicate files by name and size...")
    grouped = defaultdict(list)
    for file in files:
        key = (file['name'], file['size_bytes'])
        grouped[key].append(file)

    duplicates_to_delete = []
    total_bytes_savable = 0

    for group in grouped.values():
        if len(group) > 1:
            # Keep the first, mark the rest as duplicates
            duplicates_to_delete.extend(group[1:])
            total_bytes_savable += sum(f['size_bytes'] for f in group[1:])

    if not duplicates_to_delete:
        print("✅ No duplicate files found.")
        return

    print(f"⚠️ Found {len(duplicates_to_delete)} duplicate files.")
    print(f"💾 Estimated space that can be saved: {human_readable_size(total_bytes_savable)}")
    confirm = input("❓ Do you want to move these duplicates to trash? [y/N]: ").strip().lower()
    if confirm == 'y':
        for file in duplicates_to_delete:
            try:
                file_id = file['path'].split('/')[-2]
                service.files().update(fileId=file_id, body={'trashed': True}).execute()
                print(f"🗑️ Trashed duplicate: {file['name']} - {file['path']}")
            except Exception as e:
                print(f"❌ Failed to trash {file['name']}: {e}")
    else:
        print("🚫 No files were deleted.")


def main():
    print("🔐 Authenticating with Google Drive...")
    service = authenticate()
    gdrive_files = []

    while True:
        print("\n🎮 Choose an option:")
        print("1. Run storage audit dashboard")
        print("2. Export all image/video file info to JSON")
        print("3. Export only files larger than X MB to JSON")
        print("4. Replace first X images above X MB and reduce to 1080p")
        print("5. Find duplicate files by name and size")
        print("6. Exit")

        choice = input("👉 Enter choice [1-6]: ").strip()

        if choice == "1":
            gdrive_files = fetch_files(service, QUERY_ALL_FILES)
            export_storage_audit_dashboard(gdrive_files)

        elif choice == "2":
            gdrive_files = fetch_files(service, QUERY_MEDIA_FILES)
            export_to_json_file(gdrive_files, "all_media_files.json")

        elif choice == "3":
            threshold_str = input("📏 Enter minimum file size in MB: ").strip()
            try:
                threshold_mb = float(threshold_str)
                threshold_bytes = threshold_mb * 1024 * 1024
                if not gdrive_files:
                    gdrive_files = fetch_files(service, QUERY_ALL_FILES)
                large_files = [f for f in gdrive_files if f['size_bytes'] > threshold_bytes]
                if not large_files:
                    print("❌ No files found above the specified size.")
                else:
                    export_to_json_file(
                        large_files, f"media_files_above_{int(threshold_mb)}MB.json"
                    )
            except ValueError:
                print("❌ Invalid number entered.")

        elif choice == "4":
            number_of_files = 0
            try:
                number_of_files = int(
                    input("🔢 Enter the number of files you want to compress: ").strip()
                )
                threshold_mb = float(input("📏 Enter minimum image file size in MB: ").strip())
                gdrive_files = fetch_files(service, QUERY_MEDIA_FILES)
                download_and_reduce_images(service, gdrive_files, threshold_mb, number_of_files)
            except ValueError:
                print("❌ Invalid number entered.")

        elif choice == "5":
            gdrive_files = fetch_files(service, QUERY_ALL_FILES)
            find_duplicates(service, gdrive_files)

        elif choice == "6":
            print("👋 Exiting.")
            break

        else:
            print("❌ Invalid choice. Try again.")


if __name__ == "__main__":
    main()
