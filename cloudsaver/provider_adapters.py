from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Protocol


ProgressCallback = Callable[[dict], None] | None


@dataclass(frozen=True)
class ProviderCapabilities:
    scan: bool
    quota: bool = False
    duplicates: bool = True
    cleanup: bool = False
    restore: bool = False
    direct_api: bool = False
    local_sync: bool = False


@dataclass(frozen=True)
class ProviderScanContext:
    source_id: str
    source_type: str
    path: str | None = None
    access_token: str | None = None
    options: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderFile:
    id: str
    provider_file_id: str
    source_id: str
    source_type: str
    name: str
    path: str | None
    size_bytes: int
    modified_time: str | None = None
    mime_type: str | None = None
    checksum: str | None = None
    provider_state: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    def to_scan_dict(self) -> dict:
        data = {
            "id": self.id,
            "file_id": self.id,
            "provider_file_id": self.provider_file_id,
            "provider_identity": {
                "namespace": f"{self.source_type}:{self.source_id}",
                "source_type": self.source_type,
                "raw_id": self.provider_file_id,
                "normalized_id": self.id,
            },
            "source_id": self.source_id,
            "source_type": self.source_type,
            "name": self.name,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "mtime": self.modified_time,
            "mimeType": self.mime_type,
            "md5": self.checksum,
            "included": True,
            "provider_state": self.provider_state,
        }
        data.update(self.raw)
        return data


class ProviderAdapter(Protocol):
    key: str
    label: str
    capabilities: ProviderCapabilities

    def scan(
        self,
        context: ProviderScanContext,
        progress_callback: ProgressCallback = None,
    ) -> Iterable[ProviderFile]:
        """Yield normalized provider files for a source scan."""
