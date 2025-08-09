import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.cloudsaver import (
    export_to_json_file,
    fetch_files,
    OUTPUT_DIR,
    QUERY_ALL_FILES
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
                {"id": "1", "name": "img.png", "mimeType": "image/png", "size": "2048"},
                {"id": "2", "name": "vid.mp4", "mimeType": "video/mp4", "size": "4096"},
            ],
            "nextPageToken": None,
        }
    ]
    files = fetch_files(QUERY_ALL_FILES, mock_service)
    assert len(files) == 2
    print(files)
    assert files[0]["id"] == "1"
    assert files[0]["name"] == "img.png"
    assert files[1]["mimeType"]
