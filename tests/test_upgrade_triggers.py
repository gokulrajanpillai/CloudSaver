from pathlib import Path


APP_JS = Path(__file__).resolve().parent.parent / "web" / "app.js"
INDEX_HTML = Path(__file__).resolve().parent.parent / "web" / "index.html"


def test_upgrade_trigger_system_present():
    js = APP_JS.read_text()

    assert "const UPGRADE_TRIGGERS" in js
    assert "function checkUpgradeTriggers" in js
    assert "cloudsaver-upgrade-dismissed-" in js
    assert "state.license?.is_pro" in js


def test_upgrade_nudge_markup_present():
    html = INDEX_HTML.read_text()

    assert 'id="upgrade-nudge"' in html
    assert 'id="upgrade-nudge-message"' in html
    assert "See Pro features" in html
