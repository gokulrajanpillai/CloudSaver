#!/usr/bin/env python3
"""
Create a demo fixture folder with realistic files for CloudSaver screenshots.

Usage:
    python3 scripts/create-demo-fixture.py [--dir PATH]

This creates a throwaway folder with images, documents, duplicates, and large
files — enough to produce a meaningful scan with duplicate groups, storage map
data, and recoverable estimates. Scan it with CloudSaver to capture screenshots.

The folder contains no private data and is safe to delete when done.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import random
import shutil
import struct
import sys
import tempfile
import time
import zipfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Tiny fake-file generators (no Pillow required, but uses it when available)
# ---------------------------------------------------------------------------

def _solid_jpeg(path: Path, width: int, height: int, rgb: tuple[int, int, int]) -> None:
    """Write a minimal valid JPEG filled with one colour. Uses Pillow when available."""
    try:
        from PIL import Image
        img = Image.new("RGB", (width, height), rgb)
        img.save(path, "JPEG", quality=85)
    except ImportError:
        # Write a 1x1 white JPEG by hand (smallest valid JPEG)
        jfif = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00,
            0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB,
            0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07,
            0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B,
            0x0B, 0x0C, 0x19, 0x12, 0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E,
            0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C,
            0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34,
            0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
            0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01,
            0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05,
            0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01,
            0x03, 0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00,
            0x01, 0x7D, 0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21,
            0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
            0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1,
            0xF0, 0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16, 0x17, 0x18,
            0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35, 0x36,
            0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49,
            0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64,
            0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75, 0x76, 0x77,
            0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A,
            0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3, 0xA4,
            0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8,
            0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA,
            0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1,
            0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA,
            0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0x26, 0xA2,
            0x80, 0x00, 0xFF, 0xD9,
        ])
        path.write_bytes(jfif)


def _pad_file(path: Path, target_bytes: int) -> None:
    """Append zero bytes to reach target_bytes (for simulating large files)."""
    current = path.stat().st_size
    if current < target_bytes:
        with path.open("ab") as fh:
            fh.write(b"\x00" * (target_bytes - current))


def _make_zip(path: Path, size_bytes: int) -> None:
    """Write a minimal zip archive with a filler entry."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("data.bin", b"\x00" * max(0, size_bytes - 200))


def _text_file(path: Path, lines: int = 40) -> None:
    sentences = [
        "Meeting notes from the quarterly review.",
        "Action item: follow up on storage audit.",
        "Budget allocated for cloud storage next year.",
        "See attached report for details.",
        "Reviewed by the team on 2026-05-01.",
    ]
    content = "\n".join(sentences[i % len(sentences)] for i in range(lines))
    path.write_text(content)


# ---------------------------------------------------------------------------
# Build the fixture tree
# ---------------------------------------------------------------------------

def create_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)

    # --- Photos: 2024 trip (3 originals, 1 duplicate of trip-001) ----------
    photos = root / "Photos" / "2024-Trip"
    photos.mkdir(parents=True, exist_ok=True)

    img_colours = [
        (220, 120, 80),
        (80, 140, 200),
        (60, 180, 120),
        (200, 200, 60),
        (160, 80, 200),
    ]
    for i, colour in enumerate(img_colours, start=1):
        _solid_jpeg(photos / f"trip-{i:03d}.jpg", 3840, 2160, colour)
        _pad_file(photos / f"trip-{i:03d}.jpg", 6 * 1024 * 1024)  # ~6 MB each

    # Exact duplicate of trip-001
    shutil.copy2(photos / "trip-001.jpg", photos / "trip-001-backup.jpg")

    # Screenshots folder: smaller images
    screenshots = root / "Photos" / "Screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    for i, colour in enumerate([(240, 240, 240), (30, 30, 30), (100, 150, 250)], start=1):
        _solid_jpeg(screenshots / f"screenshot-{i:03d}.png", 1920, 1080, colour)
        _pad_file(screenshots / f"screenshot-{i:03d}.png", 800 * 1024)  # ~800 KB

    # --- Documents --------------------------------------------------------
    docs = root / "Documents"
    docs.mkdir(exist_ok=True)
    _text_file(docs / "Q1-2026-storage-review.txt", 60)
    _text_file(docs / "Q1-2026-storage-review-copy.txt", 60)  # near-duplicate
    shutil.copy2(docs / "Q1-2026-storage-review.txt", docs / "Q1-2026-storage-review-copy.txt")
    _text_file(docs / "meeting-notes-2026-01.txt", 20)
    _text_file(docs / "meeting-notes-2026-02.txt", 25)
    _text_file(docs / "meeting-notes-2026-03.txt", 22)

    # --- Archives ---------------------------------------------------------
    archives = root / "Downloads" / "Archives"
    archives.mkdir(parents=True, exist_ok=True)
    _make_zip(archives / "project-backup-2025-12.zip", 85 * 1024 * 1024)   # 85 MB
    _make_zip(archives / "project-backup-2025-11.zip", 82 * 1024 * 1024)   # 82 MB (older ver)
    _make_zip(archives / "assets-export.zip", 40 * 1024 * 1024)            # 40 MB

    # --- Old installers / large binaries ----------------------------------
    downloads = root / "Downloads"
    large = downloads / "node-v20.11.0-darwin-x64.tar"
    large.write_bytes(b"\x00")
    _pad_file(large, 55 * 1024 * 1024)  # 55 MB fake tarball

    old_dmg = downloads / "zoom-installer-old.dmg"
    old_dmg.write_bytes(b"\x00")
    _pad_file(old_dmg, 110 * 1024 * 1024)  # 110 MB - largest file

    # --- Design assets (more images, some duplicates) ---------------------
    design = root / "Design" / "Assets"
    design.mkdir(parents=True, exist_ok=True)
    _solid_jpeg(design / "hero-banner.jpg", 2560, 1440, (50, 80, 140))
    _pad_file(design / "hero-banner.jpg", 4 * 1024 * 1024)
    shutil.copy2(design / "hero-banner.jpg", design / "hero-banner-v2.jpg")  # duplicate
    _solid_jpeg(design / "logo-render.png", 800, 800, (255, 100, 50))
    _pad_file(design / "logo-render.png", 1 * 1024 * 1024)

    # --- Videos (fake, large) --------------------------------------------
    video_dir = root / "Videos"
    video_dir.mkdir(exist_ok=True)
    screencast = video_dir / "demo-screencast-2026-02.mp4"
    screencast.write_bytes(b"\x00")
    _pad_file(screencast, 220 * 1024 * 1024)  # 220 MB

    raw_export = video_dir / "raw-export-uncompressed.mov"
    raw_export.write_bytes(b"\x00")
    _pad_file(raw_export, 180 * 1024 * 1024)  # 180 MB

    # Duplicate of screencast (common "export and forget" pattern)
    shutil.copy2(screencast, video_dir / "demo-screencast-2026-02-final.mp4")


def print_instructions(root: Path) -> None:
    print()
    print("=" * 62)
    print("  CloudSaver demo fixture ready")
    print("=" * 62)
    print(f"\n  Fixture folder: {root}")
    print()
    print("  What's in it:")
    print("    Photos/        – large JPEGs + 2 duplicate groups")
    print("    Documents/     – text files + exact duplicate pair")
    print("    Downloads/     – 2 large archives + 2 large binaries")
    print("    Design/        – images with a duplicate")
    print("    Videos/        – 2 large videos + 1 duplicate screencast")
    print()

    total = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
    print(f"  Total fixture size: {total / 1024 / 1024:.0f} MB")
    print()
    print("─" * 62)
    print("  Screenshot steps")
    print("─" * 62)
    print()
    print("  1. Start the web UI:")
    print("       python3 -m cloudsaver.web_server")
    print()
    print("  2. Open: http://127.0.0.1:8765")
    print()
    print("  SCREENSHOT 1 — first-run-scan.png")
    print("    Capture the sidebar before scanning (scan controls visible).")
    print()
    print(f"  3. Enter this path and click Start scan:")
    print(f"       {root}")
    print()
    print("  SCREENSHOT 2 — scan-progress.png")
    print("    Capture the sidebar while the scan is running.")
    print()
    print("  (wait for scan to finish)")
    print()
    print("  SCREENSHOT 3 — dashboard-summary.png")
    print("    Capture the Recommended tab after scan completes.")
    print()
    print("  SCREENSHOT 4 — storage-map.png")
    print("    Click the Map tab. Capture the treemap.")
    print()
    print("  SCREENSHOT 5 — duplicate-review.png")
    print("    Click the Duplicates tab. Capture the duplicate groups")
    print("    showing recommended keep copies.")
    print()
    print("  6. Select one duplicate group and click 'Move to review'.")
    print()
    print("  SCREENSHOT 6 — review-restore.png")
    print("    Capture the Review tab showing the restore manifest.")
    print()
    print("  SCREENSHOT 7 — history.png")
    print("    Click History in the sidebar. Capture the scan history.")
    print()
    print("─" * 62)
    print("  Save screenshots to: docs/assets/")
    print("─" * 62)
    print()
    print("  When done, delete the fixture folder:")
    print(f"    rm -rf '{root}'")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create CloudSaver demo fixture folder.")
    parser.add_argument(
        "--dir",
        default=str(Path(tempfile.gettempdir()) / "cloudsaver-demo"),
        help="Where to create the fixture folder (default: system temp).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete an existing fixture folder before creating a new one.",
    )
    args = parser.parse_args()

    root = Path(args.dir).expanduser().resolve()
    if args.clean and root.exists():
        shutil.rmtree(root)

    if root.exists():
        print(f"Fixture folder already exists: {root}")
        print("Use --clean to recreate it.")
    else:
        print(f"Creating demo fixture at {root} ...")
        create_fixture(root)
        print("Done.")

    print_instructions(root)


if __name__ == "__main__":
    main()
