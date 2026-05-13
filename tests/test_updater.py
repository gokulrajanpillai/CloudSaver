import json

from cloudsaver import updater


def test_get_current_version_reads_version_file(monkeypatch, tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3")
    monkeypatch.setattr(updater, "VERSION_FILE", version_file)

    assert updater.get_current_version() == "1.2.3"


def test_version_greater_semver():
    assert updater._version_greater("1.1.0", "1.0.0") is True
    assert updater._version_greater("1.0.0", "1.0.0") is False


def test_check_for_update_with_mocked_github(monkeypatch, tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.0.0")
    monkeypatch.setattr(updater, "VERSION_FILE", version_file)

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        @staticmethod
        def read():
            return json.dumps(
                {
                    "tag_name": "v1.1.0",
                    "body": "Release notes",
                    "html_url": "https://github.com/release",
                }
            ).encode("utf-8")

    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda request, timeout: FakeResponse())

    info = updater.check_for_update()

    assert info.current_version == "1.0.0"
    assert info.latest_version == "1.1.0"
    assert info.update_available is True
    assert info.release_url == "https://github.com/release"
