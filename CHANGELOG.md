# Changelog

All notable changes to CloudSaver will be documented in this file.

CloudSaver uses semantic versioning while the project is packaged and released.

## Unreleased

- Added an embedded desktop shell entry point that reuses the local CloudSaver web UI with a browser fallback.
- Added cross-platform desktop artifact packaging for Windows, macOS, and Linux release builds.
- Marked the package maturity as Beta until signed desktop builds and consumer cleanup flows are proven.
- Clarified savings labels so image-copy estimates and storage-cost estimates are not presented as guaranteed cleanup savings.
- Refreshed scan results after quarantine and restore actions, and excluded `.cloudsaver-review` folders from future scans.
- Added duplicate-group actions that select recoverable extra copies for review from the duplicate panel.
- Moved default generated reports and reduced image copies to `~/.cloudsaver/output`, with `CLOUDSAVER_HOME` available for overrides.
- Grouped the long dashboard into named workspace views as the foundation for a tabbed cleanup workflow.
- Redesigned the sidebar around scan state and local-first safety instead of showing sponsorship before scan value.

## 1.0.0 - 2026-05-09

- Added project package metadata, compatibility setup configuration, and CLI entry points.
- Added GitHub source release workflow for version tags.
- Documented release process.
- Added a consumer-oriented local web workflow with quick scan starters, recommended cleanup guidance, reveal-in-folder file actions, and visible restore batches after files are moved to review.
- Restored release automation and aligned CI module compilation with the packaged `cloudsaver` modules.
