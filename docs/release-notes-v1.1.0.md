# CloudSaver v1.1.0 Release Notes

CloudSaver v1.1.0 is the first public release — a source-installable storage audit and
cleanup tool for local drives, synced cloud folders, external drives, and NAS mounts.

## What's New in 1.1.0

- Guided post-scan "safest next steps" panel with ranked, low-risk cleanup actions
- In-app privacy and safety links in scan controls so users can verify local-first
  guarantees before scanning
- Restore-test prompt after review moves, so users can confirm the manifest before
  manually deleting anything
- Redesigned workspace with tabs: Recommended, Map, Duplicates, Files, Review, History
- Action-first Recommended cards navigating directly into cleanup workflows
- Direct duplicate-group action to move extra copies to the review folder in one click
- Larger storage treemap with item detail panel, reveal-in-folder, and select actions
- Report exports consolidated into the Files tab
- Review batches as the primary restore UI; manual manifest restore available under advanced
- Mobile sidebar toggle with persistent scan controls on desktop
- Cross-platform desktop artifact packaging (Windows, macOS, Linux via PyInstaller)
- Embedded desktop shell entry point reusing the local web UI
- Privacy architecture and safety model documentation

## What Works

- Scan any local, mounted, external-drive, NAS, or cloud-synced folder visible to the OS
- Storage dashboard: totals, category breakdown, largest files and folders
- Storage treemap with folder drill-down and item detail
- Duplicate groups with SHA-256 verification, confidence, and recommended keep copy
- Perceptual image duplicate detection (requires `pip install cloudsaver[image_extras]`)
- Safe file review: move selected files to `.cloudsaver-review` with a restore manifest
- Restore individual files or entire review batches through the web UI
- Large image reduction to 1080p copies without modifying originals
- JSON and CSV report exports from the web UI
- Local scan history in SQLite with repeat-scan trends
- AI Storage Advisor powered by Claude (requires `ANTHROPIC_API_KEY` and Pro license)
- Team workspaces with shared audit summaries (Business license)

## Known Limitations

- Desktop builds are unsigned unless the artifact name explicitly says signed.
- Direct Google Drive, iCloud, Dropbox, OneDrive, and S3 APIs are not supported — scan
  the local synced or mounted folder instead.
- Perceptual image duplicate detection requires `pip install cloudsaver[image_extras]`.
- Video and audio savings estimates require `ffprobe` for media metadata.
- CloudSaver moves files to a local review folder only — it never permanently deletes files.
- AI Advisor and Business workspace features require a Pro or Business license key.

## Privacy Summary

The local scan and cleanup workflow does not upload file contents, filenames, file paths,
scan results, or usage events to any remote service. All optional network paths are
documented in [PRIVACY.md](../PRIVACY.md) and are disabled by default.

## Verification Checklist

```bash
python3 -m pytest              # 83 tests, all passing
npm run check:js               # JavaScript syntax
npm run test:e2e               # Playwright browser tests
./scripts/release-smoke.sh     # Startup smoke check
```
