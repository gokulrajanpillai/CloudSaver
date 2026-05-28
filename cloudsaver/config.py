from __future__ import annotations

import json
import os
from pathlib import Path


def app_data_dir() -> Path:
    """Return the local CloudSaver app-data directory."""

    return Path(os.environ.get("CLOUDSAVER_HOME", Path.home() / ".cloudsaver")).expanduser()


def app_data_path(*parts: str) -> Path:
    """Return a path inside the local CloudSaver app-data directory."""

    return app_data_dir().joinpath(*parts)


PRIVACY_SETTINGS_PATH = app_data_path("privacy_settings.json")


def load_privacy_settings() -> dict:
    """Load persisted privacy settings."""

    defaults = {
        "local_diagnostics_enabled": os.environ.get("CLOUDSAVER_NO_ANALYTICS", "") != "1"
    }
    if not PRIVACY_SETTINGS_PATH.exists():
        return defaults
    try:
        data = json.loads(PRIVACY_SETTINGS_PATH.read_text())
    except Exception:
        return defaults
    return {
        "local_diagnostics_enabled": bool(
            data.get("local_diagnostics_enabled", defaults["local_diagnostics_enabled"])
        )
    }


def save_privacy_settings(settings: dict) -> dict:
    """Persist privacy settings and return normalized values."""

    normalized = {
        "local_diagnostics_enabled": bool(settings.get("local_diagnostics_enabled", True))
    }
    PRIVACY_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRIVACY_SETTINGS_PATH.write_text(json.dumps(normalized, indent=2) + "\n")
    return normalized


def local_diagnostics_enabled() -> bool:
    """Return whether local privacy-safe diagnostics can be written."""

    if os.environ.get("CLOUDSAVER_NO_ANALYTICS", "") == "1":
        return False
    return bool(load_privacy_settings().get("local_diagnostics_enabled", True))


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
