from __future__ import annotations

import os


def feature_enabled(feature_name: str, default: bool = True) -> bool:
    """Return whether a named feature flag is enabled.

    Flags default to enabled and can be disabled with
    CLOUDSAVER_DISABLE_{FEATURE_NAME}=1.
    """

    value = os.environ.get(f"CLOUDSAVER_DISABLE_{feature_name.upper()}")
    if value is None:
        return default
    return value.strip().lower() not in {"1", "true", "yes", "on"}


SMART_SCAN_FOUNDATION = feature_enabled("SMART_SCAN_FOUNDATION")
IMAGE_EXPANSION = feature_enabled("IMAGE_EXPANSION")
MEDIA_ANALYSIS = feature_enabled("MEDIA_ANALYSIS")
