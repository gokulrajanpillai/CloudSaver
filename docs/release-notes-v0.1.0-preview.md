# CloudSaver v0.1.0-preview Release Notes

CloudSaver `v0.1.0-preview` is a source-first preview for users who want to inspect and try
a local-first storage cleanup workflow before signed convenience builds are ready.

## What Works

- Scan local, mounted, external-drive, NAS, and cloud-synced folders visible to the
  operating system.
- View a local dashboard with storage totals, category mix, largest folders, and largest
  files.
- Review duplicate candidates with verification status, confidence, and recommended keep
  copy.
- Move selected files to a local `.cloudsaver-review` folder with a restore manifest.
- Restore reviewed files from the manifest through the web UI.
- Create reduced image copies without modifying originals.
- Export JSON and CSV reports from the local web UI.
- Keep local scan history under the CloudSaver app-data directory.

## Known Limitations

- Preview builds are unsigned unless the artifact name explicitly says signed.
- Direct Google Drive, iCloud, Dropbox, OneDrive, and S3 APIs are not supported. Scan the
  local synced or mounted folder instead.
- Similar-image detection requires optional image hashing dependencies.
- Video/audio savings are estimates and require `ffprobe` for media metadata.
- CloudSaver moves files only to a local review folder; it does not permanently delete
  files.
- AI Advisor and Business workspace features are preview-gated and optional.
- Screenshots and demo assets must be finalized before tagging the release.

## Privacy Summary

The local scan and cleanup workflow does not upload file contents, file names, file paths,
scan results, or usage events to a hosted CloudSaver service. Optional network features are
documented in `PRIVACY.md`.

## Verification Before Tagging

- `python3 -m pytest`
- `npm run check:js`
- `npm run test:e2e`
- `./scripts/release-smoke.sh`

## Pilot Tracking

Use `docs/pilot-feedback.md` for observed user sessions and `docs/metrics-snapshot.md` for
weekly preview metrics.

Do not tag `v0.1.0-preview` until the required screenshots are captured and the release
checks pass.
