# CloudSaver

Open-source storage cleanup for local drives, synced cloud folders, external drives, and NAS.

![CI](https://github.com/gokulrajanpillai/CloudSaver/workflows/CI/badge.svg)
![License](https://img.shields.io/github/license/gokulrajanpillai/CloudSaver)
![Sponsors](https://img.shields.io/github/sponsors/gokulrajanpillai)

CloudSaver is an open-source, local-first storage audit and cleanup tool for people and
small teams with large local or cloud-synced folders. It scans folders your operating
system can see, including synced cloud folders, external drives, NAS mounts, and local
directories.

Files stay on your machine. CloudSaver does not upload file contents, file names, or file
paths during the local scan and cleanup workflow.

CloudSaver is tested on Linux, macOS, and Windows across supported Python versions.

## Preview Status

CloudSaver is preparing a source-first `v0.1.0-preview` release. The local scan, dashboard,
duplicate review, reversible review folder, restore manifests, and JSON/CSV exports are the
core preview workflow. Desktop artifacts are experimental and unsigned unless a release
artifact explicitly says otherwise.

Known preview boundaries:

- Direct cloud-provider APIs are not supported; scan local synced or mounted folders.
- CloudSaver does not permanently delete files by default.
- Pro, Business, payment, AI advisor, and team surfaces are optional preview workflows and
  are hidden or gated unless configured.
- Review generated reports before sharing them because local report files can include local
  paths.

## Support CloudSaver

CloudSaver is free and open source. If it helps you recover space or avoid a storage
upgrade, consider sponsoring development:

- GitHub Sponsors: https://github.com/sponsors/gokulrajanpillai
- Project issues and roadmap: https://github.com/gokulrajanpillai/CloudSaver/issues
- Sponsorship guide: [docs/sponsorship.md](docs/sponsorship.md)
- Sponsor tiers: [docs/sponsor-tiers.md](docs/sponsor-tiers.md)
- Paid convenience build policy: [docs/paid-builds.md](docs/paid-builds.md)
- Revenue and product rollout plan: [docs/revenue-rollout-plan.md](docs/revenue-rollout-plan.md)
- Commercial support: [docs/commercial-support.md](docs/commercial-support.md)
- Licensing strategy: [docs/licensing-strategy.md](docs/licensing-strategy.md)

Sponsorship funds release packaging, signed builds, platform support, documentation,
accessibility, safer cleanup workflows, and dashboard polish.

## Storage Audit Dashboard

CloudSaver can run a read-only storage audit and generate:

- `~/.cloudsaver/output/storage_audit.html`: a browser-friendly dashboard
- `~/.cloudsaver/output/storage_audit.json`: the same audit data for downstream processing

Set `CLOUDSAVER_HOME` to use a different local app-data directory for history, reports,
reduced copies, review manifests, diagnostics, license state, and team state.

The audit summarizes total storage, storage by file category, largest files, largest folders,
duplicate candidates, large files to review, and estimated recoverable space from duplicate
candidates plus image optimization. The web UI also estimates rough monthly cloud storage
cost avoided and can download local JSON or CSV reports.

## Features

- Scan any local or mounted folder
- Use the local web UI to choose common scan locations or enter a specific path
- Switch between system, light, and dark UI themes with a local browser preference
- View live scan progress while files are being analyzed
- Navigate app sections for dashboard, storage map, duplicates, files, history, and settings
- Keep recent scan summaries in a local SQLite history database
- Visualize folders and files in a browser-native storage treemap with drill-down
- Review duplicate groups with verification and confidence labels
- Move selected files to a local review folder with a restore manifest
- Restore reviewed files from a manifest through the cleanup UI
- Show non-blocking sponsorship prompts after CloudSaver has delivered scan value
- Build one-file desktop artifacts for Windows, macOS, and Linux through GitHub Actions
- Maintain package-manager templates and signing documentation for release distribution
- Export all file metadata to JSON
- Export files larger than a selected size
- Generate an HTML storage dashboard
- Download JSON and CSV reports from the local web UI
- Find duplicate candidates by file name and size, with SHA-256 verification for readable
  local candidates in the web UI
- Create reduced 1080p copies of large images in `~/.cloudsaver/output/reduced`
- Estimate per-file and selected-file size reductions before processing

CloudSaver does not delete files during duplicate scanning. Review the generated audit before
removing files manually.

## Open Source Scope

CloudSaver focuses on local and mounted storage. Direct cloud-provider APIs, hosted
dashboards, required accounts, required remote telemetry, and automatic deletion are
intentionally out of scope for now. Optional paid, license, update, AI advisor, and team
workflows are documented in [PRIVACY.md](PRIVACY.md) and should remain explicit and
disabled unless configured or invoked by the user.

See [PRIVACY.md](PRIVACY.md), [CONTRIBUTING.md](CONTRIBUTING.md),
[SECURITY.md](SECURITY.md), [DCO.md](DCO.md), [ROADMAP.md](ROADMAP.md), and
[LAUNCH.md](LAUNCH.md) before contributing or reporting sensitive issues. Product
comparison notes live in [docs/comparison.md](docs/comparison.md).

## Screenshots

Screenshots and demo GIFs are required before the first public preview tag. The capture
checklist lives in [docs/screenshots.md](docs/screenshots.md), and placeholders live under
`docs/assets/`.

Planned preview screenshots:

- First-run scan controls: `docs/assets/first-run-scan.png`
- Dashboard summary: `docs/assets/dashboard-summary.png`
- Duplicate review: `docs/assets/duplicate-review.png`
- Review and restore flow: `docs/assets/review-restore.png`

Release-note draft: [docs/release-notes-v0.1.0-preview.md](docs/release-notes-v0.1.0-preview.md).

## Usage

See [docs/install.md](docs/install.md) for platform-specific install notes.

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run the web UI:

```bash
python3 -m cloudsaver.web_server
```

Or use the startup script from a source checkout:

```bash
./scripts/start-cloudsaver.sh
```

On Windows PowerShell:

```powershell
.\scripts\start-cloudsaver.ps1
```

The startup scripts honor these environment variables:

```bash
CLOUDSAVER_HOST=127.0.0.1 CLOUDSAVER_PORT=8770 ./scripts/start-cloudsaver.sh
```

After installing CloudSaver as a package, you can also run:

```bash
cloudsaver-web
```

Then open:

```text
http://127.0.0.1:8765
```

## Theme Modes

The web UI supports System, Light, and Dark modes. System follows your operating system
preference through `prefers-color-scheme`. Manual Light or Dark choices are stored only in
your browser's `localStorage` under `cloudsaver-theme`; CloudSaver does not upload or sync
that preference.

Run the CLI:

```bash
python3 -m cloudsaver
```

Or, after package installation:

```bash
cloudsaver
```

Run the desktop-style launcher:

```bash
cloudsaver-desktop
```

When prompted, enter the folder path you want to scan. For example:

```text
/Users/you/Library/CloudStorage/GoogleDrive-you@example.com/My Drive
/Volumes/SharedDrive
/Users/you/Pictures
```

## Testing

Run the Python unit and integration tests:

```bash
python3 -m pytest
```

Run frontend syntax and browser integration tests:

```bash
npm ci
npx playwright install chromium
npm run check:js
npm run test:e2e
```

Run a local startup smoke check:

```bash
./scripts/start-cloudsaver.sh
curl -fsS http://127.0.0.1:8765/api/health
```

GitHub Actions runs the Python test matrix, web server integration tests, frontend
Playwright tests, package build, and startup smoke checks on pull requests and pushes to
`main`.

If port `8765` is already in use, set `CLOUDSAVER_PORT` before starting the UI.
