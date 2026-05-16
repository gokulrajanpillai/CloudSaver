# Safety Model

CloudSaver should make cleanup reversible by default. The product may estimate savings and
recommend review actions, but it should not silently delete user files.

## Core Safety Rules

- The scan workflow is read-only.
- Duplicate detection does not delete files.
- Image optimization creates copies; originals are not modified.
- Cleanup actions move files to a local review folder.
- Review moves write a manifest for restore.
- Restore must remain available even when paid or optional features fail.
- Protected folders and exclusions should block obviously unsafe workflows.

## Protected Paths

CloudSaver refuses or skips protected system and application paths during scan/review
operations. The default protected path list includes common macOS, Linux, and Windows
system/application locations when they exist on the current machine.

Caller-supplied protected paths can be provided by code paths that need stricter policy.

Protected path behavior:

- Refuse to scan a protected root.
- Skip protected child folders during traversal.
- Skip review moves for protected files.

## Exclusions

Scan exclusions can omit noisy or risky directories and file patterns.

Default excluded directory names include:

- `.cloudsaver-review`
- `.git`
- `.svn`
- `.hg`
- `node_modules`
- `__pycache__`

Additional glob exclusions can be supplied by callers.

## Review Folder

The review workflow moves selected files into `.cloudsaver-review` under the scan root by
default. Each move batch gets its own timestamped directory and manifest.

The manifest records:

- Scan root.
- Creation time.
- Source path.
- Review path.
- Per-file status.

## Restore

Restore reads a manifest and attempts to move reviewed files back to their original paths.

Restore behavior:

- Skip manifest entries that were not moved.
- Skip missing reviewed files.
- Skip restore when the original path already exists.
- Return per-file status so the UI can explain partial restores.

## User-Facing Warning Requirements

Before moving files to review, the UI should communicate:

- Files are moved, not permanently deleted.
- A restore manifest is written.
- The user should inspect reviewed files before deleting anything manually.
- Protected paths are skipped.

The scan controls also link to the privacy policy and safety model so users can inspect the
local-first guarantees before starting a scan.

After moving files to review, the UI should encourage a restore test before manual deletion.

Current UI behavior:

- The review queue displays a restore-test prompt after files are moved to review.
- The prompt restores the latest moved batch through the same manifest restore flow used by
  the manual restore controls.

## Release Safety Checklist

- Full Python tests pass.
- Web integration tests pass.
- Restore tests cover moved files and conflicts.
- Protected path tests cover scan refusal, scan skips, and review-move skips.
- Duplicate review shows confidence and recommended keep copy.
- Known limitations are present in release notes.
