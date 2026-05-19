import json
import os
import pytest
from unittest.mock import patch

from cloudsaver.audit import build_storage_audit, estimate_monthly_storage_cost_usd
from cloudsaver.duplicates import attach_duplicate_verification, find_perceptual_duplicates
from cloudsaver.media import estimate_audio_savings, estimate_video_savings
from cloudsaver.optimize import convert_image_format, estimate_reduction_for_file, reduce_selected_images
from cloudsaver.quarantine import quarantine_selected_files, restore_quarantine
from cloudsaver.reports import export_storage_audit_dashboard, export_to_json_file, generate_business_report
from cloudsaver.scan import hash_file_partial, is_protected_path, scan_local_folder
from cloudsaver.history import list_scan_history, save_scan_history
from cloudsaver.web_server import reveal_path_in_platform_file_manager


def test_export_to_json_file_creates_file(tmp_path):
    data = [{"name": "file1", "size_bytes": 123}]
    filename = "test.json"
    output_dir = tmp_path / "output"
    os.makedirs(output_dir, exist_ok=True)
    with patch("cloudsaver.reports.OUTPUT_DIR", str(output_dir)):
        export_to_json_file(data, filename)
        file_path = output_dir / filename
        assert file_path.exists()
        with open(file_path) as f:
            saved = json.load(f)
        assert saved == data


def test_export_to_json_file_no_data(capsys, tmp_path):
    filename = "empty.json"
    output_dir = tmp_path / "output"
    os.makedirs(output_dir, exist_ok=True)
    with patch("cloudsaver.reports.OUTPUT_DIR", str(output_dir)):
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
    assert "cache_hits" in progress_events[-1]


def test_scan_local_folder_skips_review_folder(tmp_path):
    live_file = tmp_path / "keep.txt"
    live_file.write_text("keep")
    review_dir = tmp_path / ".cloudsaver-review" / "batch"
    review_dir.mkdir(parents=True)
    reviewed_file = review_dir / "old.txt"
    reviewed_file.write_text("reviewed")

    files = scan_local_folder(str(tmp_path))

    assert [file["id"] for file in files] == ["keep.txt"]


def test_scan_local_folder_honors_exclusion_globs(tmp_path):
    keep = tmp_path / "keep.jpg"
    excluded = tmp_path / "skip.tmp"
    nested = tmp_path / "cache"
    nested.mkdir()
    nested_file = nested / "data.txt"
    keep.write_bytes(b"keep")
    excluded.write_bytes(b"skip")
    nested_file.write_text("cache")

    files = scan_local_folder(str(tmp_path), exclude_globs=["*.tmp", "cache/*"])

    assert [file["id"] for file in files] == ["keep.jpg"]


def test_scan_local_folder_skips_protected_paths(tmp_path):
    protected_dir = tmp_path / "protected"
    protected_dir.mkdir()
    (protected_dir / "secret.txt").write_text("secret")
    (tmp_path / "public.txt").write_text("public")

    files = scan_local_folder(str(tmp_path), protected_paths=[protected_dir])

    assert [file["id"] for file in files] == ["public.txt"]


def test_scan_local_folder_refuses_protected_root(tmp_path):
    with pytest.raises(ValueError, match="protected folder"):
        scan_local_folder(str(tmp_path), protected_paths=[tmp_path])


def test_is_protected_path_accepts_custom_paths(tmp_path):
    protected_dir = tmp_path / "protected"
    protected_dir.mkdir()
    child = protected_dir / "child.txt"
    child.write_text("secret")

    assert is_protected_path(child, [protected_dir]) is True
    assert is_protected_path(tmp_path / "other.txt", [protected_dir]) is False


def test_scan_local_folder_marks_hardlinks_and_audit_excludes_duplicate_inode(tmp_path):
    original = tmp_path / "original.bin"
    hardlink = tmp_path / "hardlink.bin"
    original.write_bytes(b"same-inode")
    try:
        os.link(original, hardlink)
    except OSError:
        pytest.skip("hardlinks are not supported on this filesystem")

    files = scan_local_folder(str(tmp_path), use_cache=False)
    audit = build_storage_audit(files)

    assert len(files) == 2
    assert any(file.get("hardlink") is True and file.get("included") is False for file in files)
    assert audit["summary"]["hardlink_count"] == 1
    assert audit["summary"]["hardlink_bytes_saved"] == original.stat().st_size
    assert audit["summary"]["total_bytes"] == original.stat().st_size


def test_scan_local_folder_adds_sparse_and_timestamp_metadata(tmp_path):
    sparse = tmp_path / "sparse.bin"
    with open(sparse, "wb") as file:
        file.seek((1024 * 1024) - 1)
        file.write(b"\0")

    files = scan_local_folder(str(tmp_path), use_cache=False)

    assert files[0]["atime"] > 0
    assert files[0]["mtime"] > 0
    assert files[0]["blocks_bytes"] >= 0
    assert "is_sparse" in files[0]


def test_build_storage_audit_ignores_sparse_files_for_duplicates(tmp_path):
    files = [
        {
            "id": "a.bin",
            "name": "same.bin",
            "path": str(tmp_path / "a.bin"),
            "size_bytes": 1024,
            "mimeType": "application/octet-stream",
            "included": True,
            "parents": ["root"],
            "is_sparse": True,
        },
        {
            "id": "b.bin",
            "name": "same.bin",
            "path": str(tmp_path / "b.bin"),
            "size_bytes": 1024,
            "mimeType": "application/octet-stream",
            "included": True,
            "parents": ["root"],
            "is_sparse": True,
        },
    ]

    audit = build_storage_audit(files)

    assert audit["summary"]["sparse_file_count"] == 2
    assert audit["duplicate_candidates"] == []


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
    first_dir.mkdir(parents=True)
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


def test_duplicate_candidates_recommend_primary_keep_copy(tmp_path):
    primary = tmp_path / "photos"
    backup = tmp_path / "backup"
    primary.mkdir()
    backup.mkdir()
    primary_file = primary / "photo.jpg"
    backup_file = backup / "photo.jpg"
    primary_file.write_text("same content")
    backup_file.write_text("same content")

    files = scan_local_folder(str(tmp_path), use_cache=False)
    verified_files = attach_duplicate_verification(files)
    audit = build_storage_audit(verified_files)
    candidate = audit["duplicate_candidates"][0]

    assert candidate["recommended_keep_id"] == "photos/photo.jpg"
    assert candidate["recommended_keep_path"].endswith("photos/photo.jpg")
    assert "backup" not in candidate["recommended_keep_path"]
    assert candidate["recoverable_bytes"] == backup_file.stat().st_size


def test_build_storage_audit_detects_cross_name_duplicates(tmp_path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("same content")
    second.write_text("same content")

    files = scan_local_folder(str(tmp_path), use_cache=False)
    verified_files = attach_duplicate_verification(files)
    audit = build_storage_audit(verified_files)

    assert audit["opportunities"]["duplicate_count"] == 1
    assert audit["duplicate_candidates"][0]["verification_status"] == "cross-name"
    assert audit["duplicate_candidates"][0]["confidence"] == "high"


def test_partial_hash_rejects_same_name_size_different_content(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = first_dir / "copy.txt"
    second = second_dir / "copy.txt"
    first.write_text("aa")
    second.write_text("bb")

    assert hash_file_partial(first) != hash_file_partial(second)
    files = scan_local_folder(str(tmp_path), use_cache=False)
    verified_files = attach_duplicate_verification(files)

    assert {file["duplicate_verification"]["status"] for file in verified_files} == {"rejected"}


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


def test_scan_cache_reuses_hashes_for_unchanged_files(tmp_path):
    root = tmp_path / "scan"
    first_dir = root / "first"
    second_dir = root / "second"
    first_dir.mkdir(parents=True)
    second_dir.mkdir()
    (first_dir / "copy.txt").write_text("same content")
    (second_dir / "copy.txt").write_text("same content")
    db_path = tmp_path / "history.sqlite3"

    first_scan = scan_local_folder(str(root), cache_db_path=db_path)
    attach_duplicate_verification(first_scan, cache_db_path=db_path)
    progress_events = []
    second_scan = scan_local_folder(str(root), progress_events.append, cache_db_path=db_path)

    assert len(second_scan) == 2
    assert all(file.get("cached_hash") for file in second_scan)
    assert progress_events[-1]["cache_hits"] == 2


def test_export_storage_audit_dashboard_creates_json_and_html(tmp_path):
    output_dir = tmp_path / "output"
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

    with patch("cloudsaver.reports.OUTPUT_DIR", str(output_dir)):
        audit = export_storage_audit_dashboard(files)

    json_path = output_dir / "storage_audit.json"
    html_path = output_dir / "storage_audit.html"

    assert audit["summary"]["file_count"] == 1
    assert json_path.exists()
    assert html_path.exists()
    assert "CloudSaver Storage Audit" in html_path.read_text()


def test_generate_business_report_redacts_paths(tmp_path):
    primary = tmp_path / "client" / "photos"
    backup = tmp_path / "client" / "backup"
    primary.mkdir(parents=True)
    backup.mkdir()
    (primary / "photo.jpg").write_text("same content")
    (backup / "photo.jpg").write_text("same content")

    files = attach_duplicate_verification(scan_local_folder(str(tmp_path), use_cache=False))
    audit = build_storage_audit(files)
    report_path = tmp_path / "report.md"

    result_path = generate_business_report(
        audit,
        report_path,
        root_path=str(tmp_path / "client"),
    )

    report = report_path.read_text()
    assert result_path == str(report_path)
    assert "# Business Storage Audit Report" in report
    assert "Recommended Cleanup Plan" in report
    assert str(tmp_path) not in report
    assert "photo.jpg" in report


def test_estimate_reduction_for_file_marks_supported_images():
    estimate = estimate_reduction_for_file(
        {"size_bytes": 5 * 1024 * 1024, "mimeType": "image/jpeg"}
    )

    assert estimate["supported"] is True
    assert estimate["estimated_saved_bytes"] > 0
    assert estimate["estimated_after_bytes"] < 5 * 1024 * 1024
    assert estimate["format_conversion_available"] is True
    assert estimate["target_format"] == "webp"
    assert estimate["estimated_exif_bytes"] > 0


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


def test_convert_image_format_creates_webp_copy(tmp_path):
    from PIL import Image, features

    if not features.check("webp"):
        pytest.skip("Pillow WebP support is unavailable")

    root = tmp_path / "scan"
    output_dir = tmp_path / "converted"
    image_dir = root / "photos"
    image_dir.mkdir(parents=True)
    image_path = image_dir / "large.jpg"
    Image.new("RGB", (1800, 1200), color=(45, 90, 120)).save(image_path, quality=95)

    result = convert_image_format(
        root_path=str(root),
        file_ids=["photos/large.jpg"],
        target_format="webp",
        output_dir=str(output_dir),
        max_resolution=(1024, 768),
        quality=72,
    )

    converted_path = output_dir / "photos" / "large.webp"
    assert result["results"][0]["status"] == "reduced"
    assert converted_path.exists()
    assert result["results"][0]["target_format"] == "webp"
    assert result["total_after_bytes"] < result["total_before_bytes"]


def test_perceptual_duplicates_gracefully_degrade_without_optional_dependency(tmp_path):
    files = [
        {
            "id": "a.jpg",
            "name": "a.jpg",
            "path": str(tmp_path / "a.jpg"),
            "size_bytes": 200 * 1024,
            "mimeType": "image/jpeg",
            "category": "image",
            "included": True,
            "parents": ["root"],
        }
    ]

    with patch("cloudsaver.duplicates.PERCEPTUAL_HASH_AVAILABLE", False):
        assert find_perceptual_duplicates(files) == []


def test_estimate_video_savings_for_h264_probe():
    probe = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 3840,
                "height": 2160,
                "bit_rate": "20000000",
                "duration": "120",
            }
        ],
        "format": {"size": str(300 * 1024 * 1024), "format_name": "mp4"},
    }

    estimate = estimate_video_savings(probe)

    assert estimate["codec_name"] == "h264"
    assert estimate["estimated_hevc_savings_bytes"] > 100 * 1024 * 1024
    assert estimate["transcoding_recommended"] is True


def test_estimate_audio_savings_for_flac_probe():
    probe = {
        "streams": [
            {
                "codec_type": "audio",
                "codec_name": "flac",
                "sample_rate": "48000",
                "channels": 2,
                "duration": "90",
            }
        ],
        "format": {"size": str(80 * 1024 * 1024), "bit_rate": "4000000"},
    }

    estimate = estimate_audio_savings(probe)

    assert estimate["codec_name"] == "flac"
    assert estimate["is_lossless"] is True
    assert estimate["estimated_opus_savings_bytes"] > 0


def test_build_storage_audit_includes_video_audio_opportunities():
    video_probe = {
        "streams": [{"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080}],
        "format": {"size": str(400 * 1024 * 1024), "format_name": "mp4"},
    }
    audio_probe = {
        "streams": [{"codec_type": "audio", "codec_name": "flac", "sample_rate": "44100"}],
        "format": {"size": str(40 * 1024 * 1024), "bit_rate": "2000000"},
    }
    audit = build_storage_audit(
        [
            {
                "id": "video.mp4",
                "name": "video.mp4",
                "path": "/tmp/video.mp4",
                "size_bytes": 400 * 1024 * 1024,
                "mimeType": "video/mp4",
                "included": True,
                "parents": ["root"],
                "media_probe": video_probe,
            },
            {
                "id": "audio.flac",
                "name": "audio.flac",
                "path": "/tmp/audio.flac",
                "size_bytes": 40 * 1024 * 1024,
                "mimeType": "audio/flac",
                "included": True,
                "parents": ["root"],
                "media_probe": audio_probe,
            },
        ]
    )

    assert audit["opportunities"]["video_optimization_count"] == 1
    assert audit["opportunities"]["video_optimization_bytes"] > 0
    assert audit["opportunities"]["audio_optimization_count"] == 1
    assert audit["opportunities"]["audio_optimization_bytes"] > 0


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


def test_quarantine_selected_files_skips_protected_paths(tmp_path):
    root = tmp_path / "scan"
    protected_dir = root / "protected"
    protected_dir.mkdir(parents=True)
    file_path = protected_dir / "old.txt"
    file_path.write_text("do not move")

    quarantine = quarantine_selected_files(
        str(root),
        ["protected/old.txt"],
        protected_paths=[protected_dir],
    )

    assert quarantine["quarantined_count"] == 0
    assert quarantine["results"][0]["status"] == "skipped"
    assert "protected folder" in quarantine["results"][0]["error"]
    assert file_path.read_text() == "do not move"


def test_reveal_path_opens_containing_location(tmp_path):
    file_path = tmp_path / "report.txt"
    file_path.write_text("review me")

    with patch("cloudsaver.web_server.subprocess.Popen") as popen:
        reveal_path_in_platform_file_manager(str(file_path))

    popen.assert_called_once()
