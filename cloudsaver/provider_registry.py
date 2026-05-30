from __future__ import annotations

from pathlib import Path
from typing import Iterable

from cloudsaver.provider_adapters import (
    ProgressCallback,
    ProviderAdapter,
    ProviderCapabilities,
    ProviderFile,
    ProviderScanContext,
)
from cloudsaver.scan import scan_local_folder

DRIVE_FILE_FIELDS = "files(id,name,size,mimeType,md5Checksum,parents,modifiedTime,trashed,starred)"


class LocalFolderAdapter:
    key = "local"
    label = "Local folder"
    capabilities = ProviderCapabilities(scan=True, cleanup=True, restore=True, local_sync=True)

    def scan(
        self,
        context: ProviderScanContext,
        progress_callback: ProgressCallback = None,
    ) -> Iterable[ProviderFile]:
        if not context.path:
            raise ValueError("A local path is required.")
        files = scan_local_folder(
            context.path,
            progress_callback=progress_callback,
            exclude_globs=context.options.get("exclude_globs", []),
        )
        for file in files:
            yield local_scan_file_to_provider_file(file, context.source_id, context.source_type)


class GoogleDriveLocalAdapter(LocalFolderAdapter):
    key = "gdrive_local"
    label = "Google Drive synced folder"
    capabilities = ProviderCapabilities(scan=True, duplicates=True, local_sync=True)


class ICloudSyncAdapter(LocalFolderAdapter):
    key = "icloud"
    label = "iCloud Drive synced folder"
    capabilities = ProviderCapabilities(scan=True, duplicates=True, cleanup=True, restore=True, local_sync=True)


class GoogleDriveRemoteAdapter:
    key = "google_drive"
    label = "Google Drive account"
    capabilities = ProviderCapabilities(
        scan=True,
        quota=True,
        duplicates=True,
        cleanup=True,
        direct_api=True,
    )

    def scan(
        self,
        context: ProviderScanContext,
        progress_callback: ProgressCallback = None,
    ) -> Iterable[ProviderFile]:
        service = google_drive_service(context.access_token or "")
        page_token = None
        files_scanned = 0
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
            for item in batch:
                files_scanned += 1
                yield google_drive_file_to_provider_file(item, context.source_id)
            if progress_callback:
                progress_callback(
                    {
                        "files_scanned": files_scanned,
                        "current_path": batch[-1].get("name", "") if batch else "",
                    }
                )
            page_token = response.get("nextPageToken")
            if not page_token:
                break


def local_scan_file_to_provider_file(file: dict, source_id: str, source_type: str) -> ProviderFile:
    path = file.get("path")
    raw_id = str(file.get("file_id") or path or file.get("name"))
    return ProviderFile(
        id=normalize_provider_file_id(source_type, source_id, raw_id),
        provider_file_id=raw_id,
        source_id=source_id,
        source_type=source_type,
        name=str(file.get("name") or Path(path or "").name or "Untitled"),
        path=path,
        size_bytes=int(file.get("size_bytes", 0) or 0),
        modified_time=file.get("mtime"),
        mime_type=file.get("mimeType"),
        checksum=file.get("sha256") or file.get("md5"),
        provider_state={
            "availability": "local",
            "sync": "available",
            "available_offline": True,
            "cloud_only": False,
            "remote_trash": False,
        },
        raw=file,
    )


def google_drive_file_to_provider_file(file: dict, source_id: str) -> ProviderFile:
    raw_id = file["id"]
    return ProviderFile(
        id=normalize_provider_file_id("google_drive", source_id, raw_id),
        provider_file_id=raw_id,
        source_id=source_id,
        source_type="google_drive",
        name=file.get("name", "Untitled"),
        path=file.get("name"),
        size_bytes=int(file.get("size", 0) or 0),
        modified_time=file.get("modifiedTime"),
        mime_type=file.get("mimeType", ""),
        checksum=file.get("md5Checksum"),
        provider_state={
            "availability": "remote",
            "sync": "remote_only",
            "available_offline": False,
            "cloud_only": True,
            "remote_trash": bool(file.get("trashed", False)),
            "starred": bool(file.get("starred", False)),
            "pinned": bool(file.get("starred", False)),
            "shared": len(file.get("parents", [])) > 1,
            "modified_time": file.get("modifiedTime"),
            "checksum": file.get("md5Checksum"),
        },
        raw={
            "drive_id": raw_id,
            "parents": file.get("parents", []),
        },
    )


def normalize_provider_file_id(source_type: str, source_id: str, raw_id: str) -> str:
    safe_raw = raw_id.replace("\\", "/")
    return f"{source_type}:{source_id}:{safe_raw}"


def google_drive_service(access_token: str):
    if not access_token:
        raise ValueError("A Google Drive access token is required.")
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    return build("drive", "v3", credentials=Credentials(token=access_token), cache_discovery=False)


PROVIDER_ADAPTERS: dict[str, ProviderAdapter] = {
    "local": LocalFolderAdapter(),
    "gdrive_local": GoogleDriveLocalAdapter(),
    "icloud": ICloudSyncAdapter(),
    "google_drive": GoogleDriveRemoteAdapter(),
}


def get_provider_adapter(source_type: str) -> ProviderAdapter:
    try:
        return PROVIDER_ADAPTERS[source_type]
    except KeyError as error:
        raise ValueError(f"Unsupported source type: {source_type}") from error
