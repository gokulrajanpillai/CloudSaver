from __future__ import annotations

import platform
import re
import sys
import time
from typing import Any

from cloudsaver.analytics import analytics_summary
from cloudsaver.config import load_privacy_settings
from cloudsaver.license import load_license

EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
PATH_RE = re.compile(r"(/Users/[^,\s]+|/home/[^,\s]+|[A-Za-z]:\\[^,\s]+)")


def redact_value(value: Any) -> Any:
    """Redact common private values from diagnostics payloads."""

    if isinstance(value, str):
        redacted = EMAIL_RE.sub("[redacted-email]", value)
        return PATH_RE.sub("[redacted-path]", redacted)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): redact_value(item) for key, item in value.items()}
    return value


def diagnostics_export() -> dict:
    """Build a privacy-safe support diagnostics bundle."""

    license_state = load_license()
    bundle = {
        "schema": "cloudsaver.diagnostics.v1",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "python": sys.version.split()[0],
        },
        "privacy": load_privacy_settings(),
        "license": {
            "tier": license_state.tier,
            "valid": license_state.valid,
            "expired": license_state.expired,
        },
        "analytics_summary": analytics_summary(),
        "redaction": {
            "paths": True,
            "emails": True,
            "filenames": "not_collected",
            "scan_results": "not_included",
        },
    }
    return redact_value(bundle)
