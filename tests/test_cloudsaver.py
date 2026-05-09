import json
import os
from unittest.mock import patch

from cloudsaver.core import (
    OUTPUT_DIR,
    attach_duplicate_verification,
    build_storage_audit,
    estimate_reduction_for_file,
    estimate_monthly_storage_cost_usd,
    export_storage_audit_dashboard,
    export_to_json_file,
    quarantine_selected_files,
    reduce_selected_images,
    restore_quarantine,
    scan_local_folder,
)
from cloudsaver.history import list_scan_history, save_scan_history
from cloudsaver.web_server import reveal_path_in_platform_file_manager


def test_export_to_json_file_creates_file(tmp_path):
    data = [{"name": "file1", "size_bytes": 123}]
    filename = "test.json"
    output_dir = tmp_path / OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    with patch("cloudsaver.core.OUTPUT_DIR", str(output_dir)):
        export_to_json_file(data, filename)
        file_path = output_dir / filename
        assert file_path.exists()
        with open(file_path) as f:
            saved = json.load(f)
        assert saved == data


def test_export_to_json_file_no_data(capsys, tmp_path):
    filename = "empty.json"
    output_dir = tmp_path / OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    with patch("cloudsaver.core.OUTPUT_DIR", str(output_dir)):
        export_to_json_file([], filename)
        captured = capsys.readouterr()
        assert "No data to export" in captured.out


def test_scan_local_folder_returns_file_metadata(tmp_path):
    nested_dir = tmp_path / "photos"
    nested_dir.mkdir()
    image_path = nested_dir / "image.jpg"
    document_path = tmp_path / "notes.txt"
    image_path.write_bytes(b"image-content")
    document_path.write_text("hello")

    files = scan_local_folder(str(tmp_path))

    assert len(files) == 2
    by_name = {file["name"]: file for file in files}
    assert by_name["image.jpg"]["id"] == "photos/image.jpg"
    assert by_name["image.jpg"]["parents"] == ["photos"]
    assert by_name["image.jpg"]["mimeType"] == "image/jpeg"
    assert by_name["notes.txt"]["parents"] == ["root"]


def test_scan_local_folder_reports_progress(tmp_path):
    document_path = tmp_path / "notes.txt"
    document_path.write_text("hello")
    progress_events = []

    files = scan_local_folder(str(tmp_path), progress_events.append)

    assert len(files) == 1
    assert progress_events
    assert progress_events[-1]["files_scanned"] == 1
    assert progress_events[-1]["current_path"].endswith("notes.txt")


def test_build_storage_audit_summarizes_opportunities():
    one_mb = 1024 * 1024
    files = [
        {
            "id": "photos/photo.jpg",
            "name": "photo.jpg",
            "path": "/mounted/photos/photo.jpg",
            "size_bytes": 10 * one_mb,
            "mimeType": "image/jpeg",
            "included": True,
            "parents": ["photos"],
        },
        {
            "id": "backup/photo.jpg",
            "name": "photo.jpg",
            "path": "/mounted/backup/photo.jpg",
            "size_bytes": 10 * one_mb,
            "mimeType": "image/jpeg",
            "included": True,
            "parents": ["backup"],
        },
        {
            "id": "videos/video.mp4",
            "name": "video.mp4",
            "path": "/mounted/videos/video.mp4",
            "size_bytes": 150 * one_mb,
            "mimeType": "video/mp4",
            "included": True,
            "parents": ["videos"],
        },
    ]

    audit = build_storage_audit(files, top_n=5)

    assert audit["summary"]["file_count"] == 3
    assert audit["summary"]["total_bytes"] == 170 * one_mb
    assert audit["by_category"]["video"]["bytes"] == 150 * one_mb
    assert audit["opportunities"]["duplicate_count"] == 1
    assert audit["opportunities"]["duplicate_bytes"] == 10 * one_mb
    assert audit["opportunities"]["image_optimization_count"] == 1
    assert audit["opportunities"]["large_file_count"] == 1
    assert audit["opportunities"]["estimated_monthly_cost_avoided_human"].endswith("/mo")
    assert audit["top_folders"][0]["folder_id"] == "videos"


def test_estimate_monthly_storage_cost_usd():
    assert estimate_monthly_storage_cost_usd(100 * 1024 * 1024 * 1024) == 2.5


def test_scan_history_persists_recent_scans(tmp_path):
    db_path = tmp_path / "history.sqlite3"
    audit = build_storage_audit(
        [
            {
                "id": "report.pdf",
                "name": "report.pdf",
                "path": str(tmp_path / "report.pdf"),
                "size_bytes": 2048,
                "mimeType": "application/pdf",
                "included": True,
                "parents": ["root"],
            }
        ]
    )

    history_id = save_scan_history(str(tmp_path), audit, db_path)
    history = list_scan_history(db_path=db_path)

    assert history_id == 1
    assert history[0]["root_path"] == str(tmp_path)
    assert history[0]["file_count"] == 1


def test_duplicate_verification_confirms_matching_file_content(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = first_dir / "copy.txt"
    second = second_dir / "copy.txt"
    first.write_text("same content")
    second.write_text("same content")

    files = scan_local_folder(str(tmp_path))
    verified_files = attach_duplicate_verification(files)
    audit = build_storage_audit(verified_files)

    assert audit["opportunities"]["duplicate_count"] == 1
    assert audit["duplicate_candidates"][0]["verification_status"] == "verified"
    assert audit["duplicate_candidates"][0]["verification_algorithm"] == "sha256"


def test_duplicate_verification_rejects_same_name_and_size_with_different_content(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = first_dir / "copy.txt"
    second = second_dir / "copy.txt"
    first.write_text("aa")
    second.write_text("bb")

    files = scan_local_folder(str(tmp_path))
    verified_files = attach_duplicate_verification(files)
    audit = build_storage_audit(verified_files)

    assert audit["opportunities"]["duplicate_count"] == 0
    assert audit["duplicate_candidates"] == []


def test_export_storage_audit_dashboard_creates_json_and_html(tmp_path):
    output_dir = tmp_path / OUTPUT_DIR
    files = [
        {
            "id": "report.pdf",
            "name": "report.pdf",
            "path": str(tmp_path / "report.pdf"),
            "size_bytes": 2048,
            "mimeType": "application/pdf",
            "included": True,
            "parents": ["root"],
        }
    ]

    with patch("cloudsaver.core.OUTPUT_DIR", str(output_dir)):
        audit = export_storage_audit_dashboard(files)

    json_path = output_dir / "storage_audit.json"
    html_path = output_dir / "storage_audit.html"

    assert audit["summary"]["file_count"] == 1
    assert json_path.exists()
    assert html_path.exists()
    assert "CloudSaver Storage Audit" in html_path.read_text()


def test_estimate_reduction_for_file_marks_supported_images():
    estimate = estimate_reduction_for_file(
        {"size_bytes": 5 * 1024 * 1024, "mimeType": "image/jpeg"}
    )

    assert estimate["supported"] is True
    assert estimate["estimated_saved_bytes"] > 0
    assert estimate["estimated_after_bytes"] < 5 * 1024 * 1024


def test_estimate_reduction_for_file_marks_unsupported_files():
    estimate = estimate_reduction_for_file({"size_bytes": 2048, "mimeType": "application/pdf"})

    assert estimate["supported"] is False
    assert estimate["estimated_saved_bytes"] == 0


def test_reduce_selected_images_creates_reduced_copy(tmp_path):
    from PIL import Image

    root = tmp_path / "scan"
    output_dir = tmp_path / "reduced"
    image_dir = root / "photos"
    image_dir.mkdir(parents=True)
    image_path = image_dir / "large.jpg"
    Image.new("RGB", (2200, 1400), color=(45, 90, 120)).save(image_path, quality=95)

    result = reduce_selected_images(
        root_path=str(root),
        file_ids=["photos/large.jpg"],
        output_dir=str(output_dir),
        max_resolution=(640, 480),
        quality=70,
    )

    reduced_path = output_dir / "photos" / "large.jpg"
    assert result["results"][0]["status"] == "reduced"
    assert reduced_path.exists()
    assert result["total_saved_bytes"] > 0


def test_quarantine_selected_files_can_restore(tmp_path):
    root = tmp_path / "scan"
    root.mkdir()
    file_path = root / "old.txt"
    file_path.write_text("review me")

    quarantine = quarantine_selected_files(str(root), ["old.txt"])

    assert quarantine["quarantined_count"] == 1
    assert not file_path.exists()
    manifest_path = quarantine["manifest_path"]
    restored = restore_quarantine(manifest_path)

    assert restored["results"][0]["status"] == "restored"
    assert file_path.read_text() == "review me"


def test_reveal_path_opens_containing_location(tmp_path):
    file_path = tmp_path / "report.txt"
    file_path.write_text("review me")

    with patch("cloudsaver.web_server.subprocess.Popen") as popen:
        reveal_path_in_platform_file_manager(str(file_path))

    popen.assert_called_once()
