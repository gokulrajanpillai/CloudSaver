from __future__ import annotations

import json
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cloudsaver.config import app_data_path
from cloudsaver.history import DEFAULT_HISTORY_DB, connect_history

DEVICE_ID_FILE = app_data_path("device_id")
TEAM_STATE_FILE = app_data_path("team.json")


def get_device_id() -> str:
    if DEVICE_ID_FILE.exists():
        return DEVICE_ID_FILE.read_text().strip()
    DEVICE_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    device_id = str(uuid.uuid4())
    DEVICE_ID_FILE.write_text(device_id)
    return device_id


def _invite_code() -> str:
    return secrets.token_hex(4).upper()


def _save_active_workspace(workspace_id: str, db_path: str | Path = DEFAULT_HISTORY_DB) -> None:
    if db_path != DEFAULT_HISTORY_DB:
        return
    TEAM_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEAM_STATE_FILE.write_text(json.dumps({"workspace_id": workspace_id}))


def get_active_workspace_id(db_path: str | Path = DEFAULT_HISTORY_DB) -> str | None:
    if db_path != DEFAULT_HISTORY_DB:
        with connect_history(db_path) as connection:
            row = connection.execute("SELECT id FROM team_workspaces ORDER BY created_at DESC LIMIT 1").fetchone()
            return row[0] if row else None
    try:
        return json.loads(TEAM_STATE_FILE.read_text()).get("workspace_id")
    except Exception:
        return None


def create_workspace(name: str, db_path: str | Path = DEFAULT_HISTORY_DB) -> dict[str, str]:
    workspace_id = str(uuid.uuid4())
    invite_code = _invite_code()
    now = time.time()
    device_id = get_device_id()
    with connect_history(db_path) as connection:
        connection.execute(
            "INSERT INTO team_workspaces (id, name, created_at, invite_code) VALUES (?, ?, ?, ?)",
            (workspace_id, name, now, invite_code),
        )
        connection.execute(
            """
            INSERT INTO team_members (workspace_id, device_id, display_name, joined_at, last_seen)
            VALUES (?, ?, ?, ?, ?)
            """,
            (workspace_id, device_id, "This device", now, now),
        )
    _save_active_workspace(workspace_id, db_path)
    return {"workspace_id": workspace_id, "invite_code": invite_code}


def join_workspace(
    invite_code: str,
    display_name: str | None,
    db_path: str | Path = DEFAULT_HISTORY_DB,
) -> dict[str, str]:
    now = time.time()
    device_id = get_device_id()
    with connect_history(db_path) as connection:
        row = connection.execute(
            "SELECT id, name FROM team_workspaces WHERE invite_code = ?",
            (invite_code.strip().upper(),),
        ).fetchone()
        if not row:
            raise ValueError("Team invite code was not found.")
        connection.execute(
            """
            INSERT OR REPLACE INTO team_members (workspace_id, device_id, display_name, joined_at, last_seen)
            VALUES (?, ?, ?, COALESCE((SELECT joined_at FROM team_members WHERE workspace_id = ? AND device_id = ?), ?), ?)
            """,
            (row[0], device_id, display_name or "This device", row[0], device_id, now, now),
        )
    _save_active_workspace(row[0], db_path)
    return {"workspace_id": row[0], "workspace_name": row[1]}


def team_status(db_path: str | Path = DEFAULT_HISTORY_DB) -> dict[str, Any]:
    workspace_id = get_active_workspace_id(db_path)
    if not workspace_id:
        return {"workspace": None, "members": [], "my_device_id": get_device_id()}
    with connect_history(db_path) as connection:
        workspace = connection.execute(
            "SELECT id, name, created_at, invite_code FROM team_workspaces WHERE id = ?",
            (workspace_id,),
        ).fetchone()
        members = connection.execute(
            """
            SELECT workspace_id, device_id, display_name, joined_at, last_seen
            FROM team_members
            WHERE workspace_id = ?
            ORDER BY last_seen DESC
            """,
            (workspace_id,),
        ).fetchall()
    return {
        "workspace": {
            "id": workspace[0],
            "name": workspace[1],
            "created_at": workspace[2],
            "invite_code": workspace[3],
        }
        if workspace
        else None,
        "members": [
            {
                "workspace_id": row[0],
                "device_id": row[1],
                "display_name": row[2],
                "joined_at": row[3],
                "last_seen": row[4],
            }
            for row in members
        ],
        "my_device_id": get_device_id(),
    }


def list_shared_audits(db_path: str | Path = DEFAULT_HISTORY_DB, limit: int = 10) -> list[dict[str, Any]]:
    workspace_id = get_active_workspace_id(db_path)
    if not workspace_id:
        return []
    with connect_history(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, workspace_id, device_id, scanned_at, file_count, total_bytes,
                   recoverable_bytes, cost_avoided_usd, summary_json
            FROM shared_audits
            WHERE workspace_id = ?
            ORDER BY scanned_at DESC
            LIMIT ?
            """,
            (workspace_id, limit),
        ).fetchall()
    return [
        {
            "id": row[0],
            "workspace_id": row[1],
            "device_id": row[2],
            "scanned_at": row[3],
            "file_count": row[4],
            "total_bytes": row[5],
            "recoverable_bytes": row[6],
            "cost_avoided_usd": row[7],
            "summary": json.loads(row[8]),
        }
        for row in rows
    ]


def share_audit(scan_id: int, db_path: str | Path = DEFAULT_HISTORY_DB) -> str:
    workspace_id = get_active_workspace_id(db_path)
    if not workspace_id:
        raise ValueError("Join or create a team workspace first.")
    shared_id = str(uuid.uuid4())
    device_id = get_device_id()
    with connect_history(db_path) as connection:
        scan = connection.execute(
            """
            SELECT scanned_at, file_count, total_bytes, recoverable_bytes, cost_avoided_usd, audit_json
            FROM scans
            WHERE id = ?
            """,
            (int(scan_id),),
        ).fetchone()
        if not scan:
            raise ValueError("Scan history item was not found.")
        audit = json.loads(scan[5])
        summary = {
            "summary": audit.get("summary", {}),
            "by_category": audit.get("by_category", {}),
            "opportunities": audit.get("opportunities", {}),
        }
        connection.execute(
            """
            INSERT INTO shared_audits (
                id, workspace_id, device_id, root_path, scanned_at, file_count,
                total_bytes, recoverable_bytes, cost_avoided_usd, summary_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                shared_id,
                workspace_id,
                device_id,
                "redacted",
                scan[0],
                scan[1],
                scan[2],
                scan[3],
                scan[4],
                json.dumps(summary),
            ),
        )
    return shared_id


def next_run_for_cron(cron_expression: str, now: datetime | None = None) -> float:
    minute, hour, dom, month, dow = cron_expression.split()
    if dom != "*" or month != "*":
        raise ValueError("Only * day/month cron fields are supported.")
    current = (now or datetime.now(timezone.utc)).replace(second=0, microsecond=0)
    for offset in range(1, 8 * 24 * 60):
        candidate = current + timedelta(minutes=offset)
        if minute != "*" and candidate.minute != int(minute):
            continue
        if hour != "*" and candidate.hour != int(hour):
            continue
        if dow != "*" and candidate.weekday() != (int(dow) - 1) % 7:
            continue
        return candidate.timestamp()
    raise ValueError("Could not calculate next run.")


def create_schedule(
    path: str,
    cron_expression: str,
    db_path: str | Path = DEFAULT_HISTORY_DB,
) -> str:
    workspace_id = get_active_workspace_id(db_path)
    if not workspace_id:
        raise ValueError("Join or create a team workspace first.")
    schedule_id = str(uuid.uuid4())
    with connect_history(db_path) as connection:
        connection.execute(
            """
            INSERT INTO scheduled_scans (
                id, workspace_id, device_id, path, cron_expression, last_run, next_run, enabled
            )
            VALUES (?, ?, ?, ?, ?, NULL, ?, 1)
            """,
            (
                schedule_id,
                workspace_id,
                get_device_id(),
                path,
                cron_expression,
                next_run_for_cron(cron_expression),
            ),
        )
    return schedule_id


def list_schedules(db_path: str | Path = DEFAULT_HISTORY_DB) -> list[dict[str, Any]]:
    workspace_id = get_active_workspace_id(db_path)
    if not workspace_id:
        return []
    with connect_history(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, workspace_id, device_id, path, cron_expression, last_run, next_run, enabled
            FROM scheduled_scans
            WHERE workspace_id = ?
            ORDER BY next_run ASC
            """,
            (workspace_id,),
        ).fetchall()
    return [
        {
            "id": row[0],
            "workspace_id": row[1],
            "device_id": row[2],
            "path": row[3],
            "cron_expression": row[4],
            "last_run": row[5],
            "next_run": row[6],
            "enabled": bool(row[7]),
        }
        for row in rows
    ]


def delete_schedule(schedule_id: str, db_path: str | Path = DEFAULT_HISTORY_DB) -> None:
    with connect_history(db_path) as connection:
        connection.execute("DELETE FROM scheduled_scans WHERE id = ?", (schedule_id,))


def leave_workspace(db_path: str | Path = DEFAULT_HISTORY_DB) -> None:
    workspace_id = get_active_workspace_id(db_path)
    if not workspace_id:
        return
    with connect_history(db_path) as connection:
        connection.execute(
            "DELETE FROM team_members WHERE workspace_id = ? AND device_id = ?",
            (workspace_id, get_device_id()),
        )
    if db_path == DEFAULT_HISTORY_DB:
        try:
            TEAM_STATE_FILE.unlink()
        except FileNotFoundError:
            pass


def run_scheduled_scans() -> None:
    """Placeholder scheduler loop hook; actual scan execution is wired in web_server in later work."""

    return None
