import json
import threading
import time
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, features

from cloudsaver import license as license_module
from cloudsaver.web_server import CloudSaverRequestHandler


def run_test_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), CloudSaverRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def get_json(base_url, path):
    with urlopen(f"{base_url}{path}", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(base_url, path, payload):
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def reset_license_state(monkeypatch, tmp_path):
    monkeypatch.setattr(license_module, "LICENSE_FILE", tmp_path / "license.json")
    monkeypatch.setattr(license_module, "_license_state", None)


def test_web_server_serves_app_and_health():
    server, base_url = run_test_server()
    try:
        assert get_json(base_url, "/api/health") == {"status": "ok"}
        with urlopen(f"{base_url}/", timeout=5) as response:
            html = response.read().decode("utf-8")
        assert "CloudSaver" in html
        assert 'data-theme-option="dark"' in html
        with urlopen(f"{base_url}/styles.css", timeout=5) as response:
            css = response.read().decode("utf-8")
        assert '[data-theme="dark"]' in css
        with urlopen(f"{base_url}/app.js", timeout=5) as response:
            js = response.read().decode("utf-8")
        assert "cloudsaver-theme" in js
    finally:
        server.shutdown()
        server.server_close()


def test_scan_status_requires_job_id():
    server, base_url = run_test_server()
    try:
        try:
            get_json(base_url, "/api/scan/status")
        except HTTPError as error:
            assert error.code == 400
            payload = json.loads(error.read().decode("utf-8"))
            assert "scan job id" in payload["error"]
        else:
            raise AssertionError("Expected missing job id to return HTTP 400")
    finally:
        server.shutdown()
        server.server_close()


def test_license_activation_api(monkeypatch, tmp_path):
    reset_license_state(monkeypatch, tmp_path)
    key = license_module.generate_license_key("PRO", "202612")

    server, base_url = run_test_server()
    try:
        initial = get_json(base_url, "/api/license")
        assert initial["tier"] == "FREE"
        assert initial["is_pro"] is False

        activated = post_json(
            base_url,
            "/api/license/activate",
            {"key": key, "email": "buyer@example.com"},
        )
        assert activated["success"] is True
        assert activated["tier"] == "PRO"
        assert activated["is_pro"] is True
        assert activated["expires_at"] == "2026-12"
        assert activated["email"] == "buyer@example.com"

        current = get_json(base_url, "/api/license")
        assert current["tier"] == "PRO"
        assert current["is_pro"] is True

        deactivated = post_json(base_url, "/api/license/deactivate", {})
        assert deactivated == {"success": True}
        assert get_json(base_url, "/api/license")["tier"] == "FREE"
    finally:
        server.shutdown()
        server.server_close()


def test_expired_license_activation_api(monkeypatch, tmp_path):
    reset_license_state(monkeypatch, tmp_path)
    key = license_module.generate_license_key("PRO", "200001")

    server, base_url = run_test_server()
    try:
        activated = post_json(base_url, "/api/license/activate", {"key": key})
        assert activated["success"] is True
        assert activated["expired"] is True
        assert activated["is_pro"] is False
    finally:
        server.shutdown()
        server.server_close()


def test_scan_start_completes_for_temp_directory(tmp_path):
    root = tmp_path / "scan"
    root.mkdir()
    (root / "notes.txt").write_text("hello")

    server, base_url = run_test_server()
    try:
        started = post_json(base_url, "/api/scan/start", {"path": str(root)})
        assert started["status"] == "queued"
        job_id = started["job_id"]

        deadline = time.time() + 5
        result = None
        while time.time() < deadline:
            status = get_json(base_url, f"/api/scan/status?{urlencode({'job_id': job_id})}")
            if status["status"] == "complete":
                result = status["result"]
                break
            assert status["status"] in {"queued", "scanning"}
            time.sleep(0.05)

        assert result is not None
        assert result["root_path"] == str(root.resolve())
        assert result["audit"]["summary"]["file_count"] == 1
        assert "included_count" in result["audit"]["summary"]
        assert "hardlink_count" in result["audit"]["summary"]
        assert "sparse_file_count" in result["audit"]["summary"]
        assert "cache_hits" in status
        assert result["files"][0]["name"] == "notes.txt"
        assert "atime" in result["files"][0]
        assert "mtime" in result["files"][0]
    finally:
        server.shutdown()
        server.server_close()


def test_convert_endpoint_creates_webp_copy(monkeypatch, tmp_path):
    if not features.check("webp"):
        return
    reset_license_state(monkeypatch, tmp_path)
    root = tmp_path / "scan"
    root.mkdir()
    image_path = root / "photo.jpg"
    Image.new("RGB", (1200, 900), color=(80, 120, 160)).save(image_path, quality=95)
    output_dir = tmp_path / "converted"

    server, base_url = run_test_server()
    try:
        post_json(base_url, "/api/license/activate", {"key": license_module.generate_license_key("PRO", "202612")})
        result = post_json(
            base_url,
            "/api/convert",
            {
                "root_path": str(root),
                "file_ids": ["photo.jpg"],
                "target_format": "webp",
                "output_dir": str(output_dir),
            },
        )

        assert result["results"][0]["status"] == "reduced"
        assert (output_dir / "photo.webp").exists()
        assert result["total_after_bytes"] < result["total_before_bytes"]
    finally:
        server.shutdown()
        server.server_close()


def test_pro_gated_convert_requires_license(monkeypatch, tmp_path):
    reset_license_state(monkeypatch, tmp_path)
    root = tmp_path / "scan"
    root.mkdir()

    server, base_url = run_test_server()
    try:
        try:
            post_json(base_url, "/api/convert", {"root_path": str(root), "file_ids": ["photo.jpg"]})
        except HTTPError as error:
            assert error.code == 402
            payload = json.loads(error.read().decode("utf-8"))
            assert payload["error"] == "pro_required"
        else:
            raise AssertionError("Expected convert endpoint to require Pro")
    finally:
        server.shutdown()
        server.server_close()


def test_pro_gated_convert_proceeds_after_activation(monkeypatch, tmp_path):
    reset_license_state(monkeypatch, tmp_path)
    key = license_module.generate_license_key("PRO", "202612")
    root = tmp_path / "scan"
    root.mkdir()

    server, base_url = run_test_server()
    try:
        post_json(base_url, "/api/license/activate", {"key": key})
        result = post_json(base_url, "/api/convert", {"root_path": str(root), "file_ids": ["missing.jpg"]})
        assert result["results"][0]["status"] == "skipped"
    finally:
        server.shutdown()
        server.server_close()


def test_perceptual_scan_endpoint_degrades_when_dependency_missing(monkeypatch, tmp_path):
    reset_license_state(monkeypatch, tmp_path)
    root = tmp_path / "scan"
    root.mkdir()
    Image.new("RGB", (420, 420), color=(100, 120, 140)).save(root / "photo.jpg", quality=90)

    server, base_url = run_test_server()
    try:
        post_json(base_url, "/api/license/activate", {"key": license_module.generate_license_key("PRO", "202612")})
        started = post_json(base_url, "/api/scan/perceptual", {"root_path": str(root)})
        deadline = time.time() + 5
        result = None
        while time.time() < deadline:
            status = get_json(base_url, f"/api/scan/status?{urlencode({'job_id': started['job_id']})}")
            if status["status"] == "complete":
                result = status["result"]
                break
            time.sleep(0.05)

        assert result is not None
        assert "perceptual_duplicate_groups" in result
    finally:
        server.shutdown()
        server.server_close()


def test_scan_start_includes_media_opportunity_fields_when_ffprobe_missing(tmp_path):
    root = tmp_path / "scan"
    root.mkdir()
    (root / "clip.mp4").write_bytes(b"not a real video")
    (root / "song.flac").write_bytes(b"not real audio")

    server, base_url = run_test_server()
    try:
        started = post_json(base_url, "/api/scan/start", {"path": str(root)})
        deadline = time.time() + 5
        result = None
        while time.time() < deadline:
            status = get_json(base_url, f"/api/scan/status?{urlencode({'job_id': started['job_id']})}")
            if status["status"] == "complete":
                result = status["result"]
                break
            time.sleep(0.05)

        assert result is not None
        opportunities = result["audit"]["opportunities"]
        assert "video_optimization_bytes" in opportunities
        assert "audio_optimization_bytes" in opportunities
        assert opportunities["video_optimization_bytes"] >= 0
        assert opportunities["audio_optimization_bytes"] >= 0
    finally:
        server.shutdown()
        server.server_close()
