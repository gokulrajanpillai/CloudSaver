# Launch Plan

CloudSaver's first public milestone should be a preview release, not a broad consumer
launch.

## Preview Release Goal

Publish `v0.1.0-preview` with enough polish for open-source users to try, inspect, and
sponsor the project.

## Required Before Tagging

- Run `./scripts/release-smoke.sh`.
- Add current dashboard screenshots under `docs/assets/`.
- Add a short demo GIF or screenshot strip to `README.md`.
- Confirm GitHub Actions CI is green on `main`.
- Confirm release workflows have `contents: write` permission.
- Confirm package artifacts build on Linux, macOS, and Windows.
- Write release notes in `CHANGELOG.md`.
- Confirm `README.md`, `PRIVACY.md`, and `docs/licensing-strategy.md` match product behavior.

## GitHub Repository Setup

Set repository topics:

- `storage`
- `disk-usage`
- `privacy`
- `local-first`
- `duplicates`
- `cleanup`
- `desktop-app`
- `open-source`

Recommended labels:

- `good first issue`
- `sponsor-needed`
- `privacy`
- `platform:macos`
- `platform:windows`
- `platform:linux`
- `ux`
- `release`

Enable GitHub Discussions after the preview release if users start opening support-style
issues.

## Launch Copy

Short description:

> Open-source, local-first storage insight for local drives, synced cloud folders, external
> drives, and NAS.

Longer description:

> CloudSaver helps users scan local or mounted folders, understand where storage is going,
> review duplicate candidates, reduce large images, and move files to a reversible review
> folder without uploading file names, paths, or contents.

## Announcement Channels

- GitHub Release notes
- GitHub Discussions
- README update
- Show HN after screenshots and release artifacts are stable
- Indie Hackers after sponsor tiers are active
- Product Hunt later, after signed builds are available

## Manual Stop Point

Creating the public version tag and release should be done intentionally by a maintainer:

```bash
git tag v0.1.0-preview
git push origin v0.1.0-preview
```

Do not tag a release until screenshots and release notes are ready.
