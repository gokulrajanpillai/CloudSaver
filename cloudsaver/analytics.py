from __future__ import annotations

"""
Privacy-first usage analytics.
Collected: feature usage counts, scan performance metrics, error types.
Never collected: file names, paths, user IDs, IP addresses, email addresses.
"""

import hashlib
import json
import os
import sqlite3
import time
import uuid

from cloudsaver.config import app_data_path

ANALYTICS_ENABLED = os.environ.get("CLOUDSAVER_NO_ANALYTICS", "") != "1"
ANALYTICS_DB = app_data_path("analytics.sqlite3")
INSTALL_ID_FILE = app_data_path("install_id")


def get_install_id() -> str:
    """One-time random ID generated per installation, salted and hashed."""

    INSTALL_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    if INSTALL_ID_FILE.exists():
        return INSTALL_ID_FILE.read_text().strip()
    raw = str(uuid.uuid4())
    salt = "cs-anon-salt-2024"
    hashed = hashlib.sha256(f"{salt}{raw}".encode()).hexdigest()[:16]
    INSTALL_ID_FILE.write_text(hashed)
    return hashed


def record_event(event_name: str, properties: dict | None = None) -> None:
    """Record an anonymous event to local SQLite."""

    if not ANALYTICS_ENABLED:
        return
    props = properties or {}
    safe_props = {
        key: value
        for key, value in props.items()
        if isinstance(value, (int, float, bool)) or key in {"feature", "tier", "error_type"}
    }
    try:
        ANALYTICS_DB.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(ANALYTICS_DB)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT NOT NULL,
                    install_id TEXT NOT NULL,
                    properties_json TEXT,
                    recorded_at REAL NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO events (event_name, install_id, properties_json, recorded_at)
                VALUES (?, ?, ?, ?)
                """,
                (event_name, get_install_id(), json.dumps(safe_props), time.time()),
            )
    except Exception:
        pass


def analytics_summary() -> dict:
    """Return local aggregate analytics for diagnostics/admin views."""

    if not ANALYTICS_DB.exists():
        return {"total_scans": 0, "total_gb_recovered": 0, "feature_usage_counts": {}}
    try:
        with sqlite3.connect(str(ANALYTICS_DB)) as connection:
            rows = connection.execute("SELECT event_name, properties_json FROM events").fetchall()
    except Exception:
        return {"total_scans": 0, "total_gb_recovered": 0, "feature_usage_counts": {}}

    total_scans = 0
    total_gb_recovered = 0
    feature_usage_counts = {}
    for event_name, properties_json in rows:
        props = json.loads(properties_json or "{}")
        if event_name == "scan_completed":
            total_scans += 1
        if event_name in {"reduce_completed", "quarantine_completed"}:
            total_gb_recovered += int(props.get("saved_gb", 0) or 0)
        if event_name == "pro_feature_used":
            feature = props.get("feature") or "unknown"
            feature_usage_counts[feature] = feature_usage_counts.get(feature, 0) + 1
    return {
        "total_scans": total_scans,
        "total_gb_recovered": total_gb_recovered,
        "feature_usage_counts": feature_usage_counts,
    }
