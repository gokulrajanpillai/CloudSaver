import importlib
import json
import sqlite3

from cloudsaver import analytics


def reset_analytics(monkeypatch, tmp_path):
    monkeypatch.setattr(analytics, "ANALYTICS_DB", tmp_path / "analytics.sqlite3")
    monkeypatch.setattr(analytics, "INSTALL_ID_FILE", tmp_path / "install_id")
    monkeypatch.setattr(analytics, "ANALYTICS_ENABLED", True)


def test_record_event_scrubs_path_properties(monkeypatch, tmp_path):
    reset_analytics(monkeypatch, tmp_path)

    analytics.record_event(
        "scan_completed",
        {"path": "/Users/me/secret", "file_count": 10, "feature": "scan"},
    )

    with sqlite3.connect(str(analytics.ANALYTICS_DB)) as connection:
        row = connection.execute("SELECT properties_json FROM events").fetchone()
    props = json.loads(row[0])

    assert "path" not in props
    assert props["file_count"] == 10
    assert props["feature"] == "scan"


def test_analytics_opt_out_disables_writes(monkeypatch, tmp_path):
    reset_analytics(monkeypatch, tmp_path)
    monkeypatch.setattr(analytics, "ANALYTICS_ENABLED", False)

    analytics.record_event("scan_completed", {"file_count": 1})

    assert not analytics.ANALYTICS_DB.exists()


def test_install_id_is_stable(monkeypatch, tmp_path):
    reset_analytics(monkeypatch, tmp_path)

    first = analytics.get_install_id()
    second = analytics.get_install_id()

    assert first == second


def test_two_installs_produce_different_ids(monkeypatch, tmp_path):
    reset_analytics(monkeypatch, tmp_path / "one")
    first = analytics.get_install_id()
    reset_analytics(monkeypatch, tmp_path / "two")
    second = analytics.get_install_id()

    assert first != second


def test_environment_opt_out_on_reload(monkeypatch):
    monkeypatch.setenv("CLOUDSAVER_NO_ANALYTICS", "1")
    reloaded = importlib.reload(analytics)

    assert reloaded.ANALYTICS_ENABLED is False

    monkeypatch.delenv("CLOUDSAVER_NO_ANALYTICS", raising=False)
    importlib.reload(analytics)
