from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


DEFAULT_HISTORY_DB = Path.home() / ".cloudsaver" / "history.sqlite3"


def connect_history(db_path: str | Path = DEFAULT_HISTORY_DB) -> sqlite3.Connection:
    """Open the local scan history database and ensure its schema exists."""

    path = Path(db_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_path TEXT NOT NULL,
            scanned_at REAL NOT NULL,
            file_count INTEGER NOT NULL,
            total_bytes INTEGER NOT NULL,
            recoverable_bytes INTEGER NOT NULL,
            cost_avoided_usd REAL NOT NULL,
            audit_json TEXT NOT NULL
        )
        """
    )
    return connection


def save_scan_history(
    root_path: str,
    audit: dict[str, Any],
    db_path: str | Path = DEFAULT_HISTORY_DB,
) -> int:
    """Persist a scan summary and return its database id."""

    summary = audit["summary"]
    opportunities = audit["opportunities"]
    with connect_history(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO scans (
                root_path,
                scanned_at,
                file_count,
                total_bytes,
                recoverable_bytes,
                cost_avoided_usd,
                audit_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                root_path,
                time.time(),
                int(summary["file_count"]),
                int(summary["total_bytes"]),
                int(opportunities["estimated_recoverable_bytes"]),
                float(opportunities["estimated_monthly_cost_avoided_usd"]),
                json.dumps(audit),
            ),
        )
        return int(cursor.lastrowid)


def list_scan_history(
    limit: int = 10,
    db_path: str | Path = DEFAULT_HISTORY_DB,
) -> list[dict[str, Any]]:
    """Return recent local scan summaries."""

    with connect_history(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, root_path, scanned_at, file_count, total_bytes, recoverable_bytes, cost_avoided_usd
            FROM scans
            ORDER BY scanned_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "id": row[0],
            "root_path": row[1],
            "scanned_at": row[2],
            "file_count": row[3],
            "total_bytes": row[4],
            "recoverable_bytes": row[5],
            "cost_avoided_usd": row[6],
        }
        for row in rows
    ]
