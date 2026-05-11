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
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS file_cache (
            root_path TEXT NOT NULL,
            relative_id TEXT NOT NULL,
            mtime REAL NOT NULL,
            size_bytes INTEGER NOT NULL,
            sha256 TEXT,
            atime REAL,
            last_seen REAL NOT NULL,
            PRIMARY KEY (root_path, relative_id)
        )
        """
    )
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(file_cache)").fetchall()
    }
    if "ffprobe_json" not in columns:
        connection.execute("ALTER TABLE file_cache ADD COLUMN ffprobe_json TEXT")
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


def save_file_cache(
    root_path: str,
    files: list[dict[str, Any]],
    db_path: str | Path = DEFAULT_HISTORY_DB,
) -> None:
    """Upsert file metadata used to skip unchanged hash work on future scans."""

    now = time.time()
    rows = [
        (
            root_path,
            file.get("id") or "",
            float(file.get("mtime", 0) or 0),
            int(file.get("size_bytes", 0) or 0),
            file.get("cached_hash")
            or (file.get("duplicate_verification") or {}).get("content_hash"),
            float(file.get("atime", 0) or 0),
            now,
            json.dumps(file.get("media_probe")) if file.get("media_probe") else None,
        )
        for file in files
        if file.get("id")
    ]
    if not rows:
        return
    with connect_history(db_path) as connection:
        connection.executemany(
            """
            INSERT INTO file_cache (
                root_path,
                relative_id,
                mtime,
                size_bytes,
                sha256,
                atime,
                last_seen,
                ffprobe_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(root_path, relative_id) DO UPDATE SET
                mtime = excluded.mtime,
                size_bytes = excluded.size_bytes,
                sha256 = excluded.sha256,
                atime = excluded.atime,
                last_seen = excluded.last_seen,
                ffprobe_json = excluded.ffprobe_json
            """,
            rows,
        )


def load_file_cache(
    root_path: str,
    db_path: str | Path = DEFAULT_HISTORY_DB,
) -> dict[str, dict[str, Any]]:
    """Return cached file metadata keyed by scan-relative id."""

    with connect_history(db_path) as connection:
        rows = connection.execute(
            """
            SELECT relative_id, mtime, size_bytes, sha256, atime, last_seen, ffprobe_json
            FROM file_cache
            WHERE root_path = ?
            """,
            (root_path,),
        ).fetchall()

    return {
        row[0]: {
            "mtime": row[1],
            "size_bytes": row[2],
            "sha256": row[3],
            "atime": row[4],
            "last_seen": row[5],
            "ffprobe_json": json.loads(row[6]) if row[6] else None,
        }
        for row in rows
    }


def prune_file_cache(
    root_path: str,
    current_ids: set[str] | list[str],
    db_path: str | Path = DEFAULT_HISTORY_DB,
) -> None:
    """Remove cached rows not present in the current scan."""

    current_ids = set(current_ids)
    with connect_history(db_path) as connection:
        if not current_ids:
            connection.execute("DELETE FROM file_cache WHERE root_path = ?", (root_path,))
            return
        placeholders = ",".join("?" for _ in current_ids)
        connection.execute(
            f"""
            DELETE FROM file_cache
            WHERE root_path = ?
            AND relative_id NOT IN ({placeholders})
            """,
            (root_path, *current_ids),
        )
