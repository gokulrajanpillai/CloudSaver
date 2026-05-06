import os
import json
from unittest.mock import patch, MagicMock
from src.cloudsaver import (
    build_storage_audit,
    export_to_json_file,
    export_storage_audit_dashboard,
    fetch_files,
    OUTPUT_DIR,
    QUERY_ALL_FILES,
)


# Test: export_to_json_file_creates_file
# This test checks that export_to_json_file creates a JSON file with the correct data in the output directory.
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


# Test: export_to_json_file_no_data
# This test ensures that export_to_json_file prints an error message when given empty data.
def test_export_to_json_file_no_data(capsys, tmp_path):
    filename = "empty.json"
    output_dir = tmp_path / OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    with patch("src.cloudsaver.OUTPUT_DIR", str(output_dir)):
        export_to_json_file([], filename)
        captured = capsys.readouterr()
        assert "No data to export" in captured.out


# Test: fetch_files_returns_files
# This test mocks the Google Drive API service and verifies that fetch_files returns the expected file info.
def test_fetch_files_returns_files():
    mock_service = MagicMock()
    mock_service.files().list().execute.side_effect = [
        {
            "files": [
                {
                    "id": "1",
                    "name": "img.png",
                    "mimeType": "image/png",
                    "size": "2048",
                    "ownedByMe": True,
                    "parents": ["folder-a"],
                },
                {
                    "id": "2",
                    "name": "vid.mp4",
                    "mimeType": "video/mp4",
                    "size": "4096",
                    "ownedByMe": True,
                    "parents": ["folder-b"],
                },
            ],
            "nextPageToken": None,
        }
    ]
    files = fetch_files(mock_service, QUERY_ALL_FILES)
    assert len(files) == 2
    assert files[0]["id"] == "1"
    assert files[0]["name"] == "img.png"
    assert files[1]["mimeType"]


def test_build_storage_audit_summarizes_opportunities():
    one_mb = 1024 * 1024
    files = [
        {
            "id": "1",
            "name": "photo.jpg",
            "path": "https://drive.google.com/file/d/1/view",
            "size_bytes": 10 * one_mb,
            "mimeType": "image/jpeg",
            "ownedByMe": True,
            "parents": ["folder-a"],
        },
        {
            "id": "2",
            "name": "photo.jpg",
            "path": "https://drive.google.com/file/d/2/view",
            "size_bytes": 10 * one_mb,
            "mimeType": "image/jpeg",
            "ownedByMe": True,
            "parents": ["folder-a"],
        },
        {
            "id": "3",
            "name": "video.mp4",
            "path": "https://drive.google.com/file/d/3/view",
            "size_bytes": 150 * one_mb,
            "mimeType": "video/mp4",
            "ownedByMe": True,
            "parents": ["folder-b"],
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
    assert audit["top_folders"][0]["folder_id"] == "folder-b"


def test_export_storage_audit_dashboard_creates_json_and_html(tmp_path):
    output_dir = tmp_path / OUTPUT_DIR
    files = [
        {
            "id": "1",
            "name": "report.pdf",
            "path": "https://drive.google.com/file/d/1/view",
            "size_bytes": 2048,
            "mimeType": "application/pdf",
            "ownedByMe": True,
            "parents": ["folder-a"],
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
