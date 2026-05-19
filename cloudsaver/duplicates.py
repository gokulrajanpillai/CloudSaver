from cloudsaver import _core_impl as _impl
from cloudsaver._core_impl import (
    PERCEPTUAL_HASH_AVAILABLE,
    attach_duplicate_verification,
    duplicate_keep_recommendation,
    find_perceptual_duplicates,
    compute_perceptual_hashes,
    _phash_distance,
    find_duplicates,
    hash_file_sha256,
)


def _sync_globals() -> None:
    _impl.PERCEPTUAL_HASH_AVAILABLE = PERCEPTUAL_HASH_AVAILABLE


def find_perceptual_duplicates(files, threshold=10):
    _sync_globals()
    return _impl.find_perceptual_duplicates(files, threshold)

__all__ = [
    'PERCEPTUAL_HASH_AVAILABLE',
    'attach_duplicate_verification',
    'duplicate_keep_recommendation',
    'find_perceptual_duplicates',
    'compute_perceptual_hashes',
    'find_duplicates',
    'hash_file_sha256',
]
