import json
from datetime import datetime, timezone

from cloudsaver import team
from cloudsaver.history import connect_history


def table_names(connection):
    return {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }


def test_team_schema_tables_created(tmp_path):
    with connect_history(tmp_path / "history.sqlite3") as connection:
        names = table_names(connection)

    assert "team_workspaces" in names
    assert "team_members" in names
    assert "shared_audits" in names
    assert "scheduled_scans" in names


def test_create_and_join_workspace(monkeypatch, tmp_path):
    db_path = tmp_path / "history.sqlite3"
    monkeypatch.setattr(team, "DEVICE_ID_FILE", tmp_path / "device_id")

    created = team.create_workspace("Acme", db_path)
    joined = team.join_workspace(created["invite_code"], "Laptop", db_path)
    status = team.team_status(db_path)

    assert joined["workspace_id"] == created["workspace_id"]
    assert status["workspace"]["name"] == "Acme"
    assert len(status["members"]) == 1


def test_share_audit_omits_file_names_and_paths(monkeypatch, tmp_path):
    db_path = tmp_path / "history.sqlite3"
    monkeypatch.setattr(team, "DEVICE_ID_FILE", tmp_path / "device_id")
    workspace = team.create_workspace("Acme", db_path)
    audit = {
        "summary": {"file_count": 1, "total_bytes": 100, "total_human": "100 B"},
        "by_category": {"image": {"count": 1, "bytes": 100}},
        "opportunities": {"estimated_recoverable_bytes": 20},
        "top_files": [{"name": "secret.jpg", "path": "/Users/me/secret.jpg"}],
    }
    with connect_history(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO scans (
                root_path, scanned_at, file_count, total_bytes, recoverable_bytes,
                cost_avoided_usd, audit_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("/Users/me", 1.0, 1, 100, 20, 0.1, json.dumps(audit)),
        )
        scan_id = cursor.lastrowid

    shared_id = team.share_audit(scan_id, db_path)
    shared = team.list_shared_audits(db_path)
    encoded = json.dumps(shared)

    assert workspace["workspace_id"]
    assert shared[0]["id"] == shared_id
    assert "secret.jpg" not in encoded
    assert "/Users/me" not in encoded


def test_next_run_for_weekly_cron():
    now = datetime(2026, 5, 13, 12, 0, tzinfo=timezone.utc)
    next_run = datetime.fromtimestamp(team.next_run_for_cron("0 2 * * 0", now), timezone.utc)

    assert next_run.weekday() == 6
    assert next_run.hour == 2
    assert next_run.minute == 0
