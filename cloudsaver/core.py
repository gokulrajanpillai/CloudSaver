from __future__ import annotations

from cloudsaver import _core_impl as _impl
from cloudsaver.audit import *
from cloudsaver.duplicates import *
from cloudsaver.media import *
from cloudsaver.optimize import *
from cloudsaver.quarantine import *
from cloudsaver.reports import *
from cloudsaver.scan import *
from cloudsaver._core_impl import (
    APP_DATA_DIR,
    AVIF_AVAILABLE,
    CLOUD_STORAGE_COST_PER_GB_MONTH_USD,
    DEFAULT_AUDIT_TOP_N,
    DEFAULT_EXCLUDED_DIR_NAMES,
    DEFAULT_IMAGE_QUALITY,
    DEFAULT_PROTECTED_PATHS,
    FFPROBE_AVAILABLE,
    HASH_CHUNK_SIZE,
    HD_RESOLUTION,
    IMAGE_OPTIMIZATION_SAVINGS_RATE,
    LARGE_FILE_THRESHOLD_BYTES,
    MEDIA_ANALYSIS,
    OUTPUT_DIR,
    OXIPNG_AVAILABLE,
    PERCEPTUAL_HASH_AVAILABLE,
    PIEXIF_AVAILABLE,
    QUARANTINE_DIR_NAME,
    REDUCED_DIR,
    SMART_SCAN_FOUNDATION,
    SUPPORTED_IMAGE_MIME_TYPES,
    main,
    prompt_for_folder,
)


def _sync_patchable_globals() -> None:
    _impl.OUTPUT_DIR = OUTPUT_DIR
    _impl.PERCEPTUAL_HASH_AVAILABLE = PERCEPTUAL_HASH_AVAILABLE


def export_to_json_file(data, filename):
    _sync_patchable_globals()
    return _impl.export_to_json_file(data, filename)


def export_storage_audit_dashboard(files):
    _sync_patchable_globals()
    return _impl.export_storage_audit_dashboard(files)


def find_perceptual_duplicates(files, threshold=10):
    _sync_patchable_globals()
    return _impl.find_perceptual_duplicates(files, threshold)


__all__ = [name for name in globals() if not name.startswith('_')]


if __name__ == "__main__":
    main()
