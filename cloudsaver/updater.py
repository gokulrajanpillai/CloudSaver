from __future__ import annotations

"""
Auto-update check - polls GitHub Releases API for new versions.
No user data is sent. Only requests: GET /repos/{owner}/{repo}/releases/latest
"""

import json
import threading
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

GITHUB_RELEASES_URL = "https://api.github.com/repos/gokulrajanpillai/CloudSaver/releases/latest"
UPDATE_CHECK_INTERVAL = 24 * 3600
VERSION_FILE = Path(__file__).parent / "VERSION"


@dataclass
class UpdateInfo:
    current_version: str
    latest_version: str
    update_available: bool
    release_url: str | None
    release_notes: str | None


def get_current_version() -> str:
    try:
        return VERSION_FILE.read_text().strip()
    except FileNotFoundError:
        return "0.0.0"


def check_for_update() -> UpdateInfo:
    """Non-blocking HTTP call to GitHub API. Returns UpdateInfo."""

    current = get_current_version()
    try:
        request = urllib.request.Request(
            GITHUB_RELEASES_URL,
            headers={"User-Agent": "CloudSaver update checker"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read())
        latest = data.get("tag_name", "").lstrip("v")
        notes = data.get("body", "")[:500]
        url = data.get("html_url")
        available = _version_greater(latest, current)
        return UpdateInfo(current, latest, available, url if available else None, notes if available else None)
    except Exception:
        return UpdateInfo(current, current, False, None, None)


def _version_greater(a: str, b: str) -> bool:
    """Returns True if version a > version b (semver comparison)."""

    try:
        return tuple(int(x) for x in a.split(".")) > tuple(int(x) for x in b.split("."))
    except ValueError:
        return False


_update_state: UpdateInfo | None = None


def start_background_update_check() -> None:
    """Start a daemon thread that checks for updates periodically."""

    def loop():
        global _update_state
        while True:
            _update_state = check_for_update()
            time.sleep(UPDATE_CHECK_INTERVAL)

    threading.Thread(target=loop, daemon=True).start()


def get_update_state() -> UpdateInfo | None:
    return _update_state


def update_info_dict(info: UpdateInfo | None = None) -> dict:
    return asdict(info or _update_state or UpdateInfo(get_current_version(), get_current_version(), False, None, None))
