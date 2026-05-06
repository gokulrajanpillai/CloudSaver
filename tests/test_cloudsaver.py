import json
import os
from unittest.mock import patch

from src.cloudsaver import (
    OUTPUT_DIR,
    build_storage_audit,
    export_storage_audit_dashboard,
    export_to_json_file,
    scan_local_folder,
)


def test_export_to_json_file_creates_file(tmp_path):
    data = [{"name": "file1", "size_bytes": 123}]
    filename = "test.json"
    output_dir = tmp_path / OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    with patch("src.cloudsaver.OUTPUT_DIR", str(output_dir)):
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
    with patch("src.cloudsaver.OUTPUT_DIR", str(output_dir)):
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
    assert audit["top_folders"][0]["folder_id"] == "videos"


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

    with patch("src.cloudsaver.OUTPUT_DIR", str(output_dir)):
        audit = export_storage_audit_dashboard(files)

    json_path = output_dir / "storage_audit.json"
    html_path = output_dir / "storage_audit.html"

    assert audit["summary"]["file_count"] == 1
    assert json_path.exists()
    assert html_path.exists()
    assert "CloudSaver Storage Audit" in html_path.read_text()
