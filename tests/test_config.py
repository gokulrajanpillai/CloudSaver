import importlib

from cloudsaver import config


def test_app_data_path_defaults_to_home_cloudsaver(monkeypatch):
    monkeypatch.delenv("CLOUDSAVER_HOME", raising=False)

    path = config.app_data_path("history.sqlite3")

    assert path.name == "history.sqlite3"
    assert path.parent.name == ".cloudsaver"


def test_app_data_path_honors_cloudsaver_home(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUDSAVER_HOME", str(tmp_path))

    assert config.app_data_path("nested", "file.json") == tmp_path / "nested" / "file.json"


def test_module_defaults_honor_cloudsaver_home_on_import(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUDSAVER_HOME", str(tmp_path))

    from cloudsaver import analytics, history, license as license_module, team

    reloaded_history = importlib.reload(history)
    reloaded_analytics = importlib.reload(analytics)
    reloaded_license = importlib.reload(license_module)
    reloaded_team = importlib.reload(team)

    assert reloaded_history.DEFAULT_HISTORY_DB == tmp_path / "history.sqlite3"
    assert reloaded_analytics.ANALYTICS_DB == tmp_path / "analytics.sqlite3"
    assert reloaded_analytics.INSTALL_ID_FILE == tmp_path / "install_id"
    assert reloaded_license.LICENSE_FILE == tmp_path / "license.json"
    assert reloaded_team.DEVICE_ID_FILE == tmp_path / "device_id"
    assert reloaded_team.TEAM_STATE_FILE == tmp_path / "team.json"
