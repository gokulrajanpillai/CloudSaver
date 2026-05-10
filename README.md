# CloudSaver

Open-source storage insight for local drives, synced cloud folders, external drives, and NAS.

![CI](https://github.com/gokulrajanpillai/CloudSaver/workflows/CI/badge.svg)
![License](https://img.shields.io/github/license/gokulrajanpillai/CloudSaver)
![Sponsors](https://img.shields.io/github/sponsors/gokulrajanpillai)

CloudSaver is an open-source, local-first storage audit and optimization tool. It scans
folders your operating system can see, including synced cloud folders, external drives,
NAS mounts, and local directories.

Files stay on your machine. CloudSaver does not upload file contents, file names, or file
paths to a hosted service.

CloudSaver is tested on Linux, macOS, and Windows across supported Python versions.

## Support CloudSaver

CloudSaver is free and open source. If it helps you recover space or avoid a storage
upgrade, consider sponsoring development:

- GitHub Sponsors: https://github.com/sponsors/gokulrajanpillai
- Project issues and roadmap: https://github.com/gokulrajanpillai/CloudSaver/issues
- Sponsorship guide: [docs/sponsorship.md](docs/sponsorship.md)
- Sponsor tiers: [docs/sponsor-tiers.md](docs/sponsor-tiers.md)
- Paid convenience build policy: [docs/paid-builds.md](docs/paid-builds.md)
- Commercial support: [docs/commercial-support.md](docs/commercial-support.md)
- Licensing strategy: [docs/licensing-strategy.md](docs/licensing-strategy.md)

Sponsorship funds release packaging, signed builds, platform support, documentation,
accessibility, safer cleanup workflows, and dashboard polish.

## Storage Audit Dashboard

CloudSaver can run a read-only storage audit and generate:

- `~/.cloudsaver/output/storage_audit.html`: a browser-friendly dashboard
- `~/.cloudsaver/output/storage_audit.json`: the same audit data for downstream processing

The audit summarizes total storage, storage by file category, largest files, largest folders,
duplicate candidates, large files to review, and estimated recoverable space from duplicate
candidates plus image optimization. The web UI also estimates rough monthly cloud storage
cost avoided and can download local JSON or CSV reports.

## Features

- Scan any local or mounted folder
- Use the local web UI to choose common scan locations or enter a specific path
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

CloudSaver focuses on local and mounted storage. Direct cloud-provider APIs, user accounts,
hosted dashboards, telemetry, and automatic deletion are intentionally out of scope for now.

See [PRIVACY.md](PRIVACY.md), [CONTRIBUTING.md](CONTRIBUTING.md),
[SECURITY.md](SECURITY.md), [DCO.md](DCO.md), [ROADMAP.md](ROADMAP.md), and
[LAUNCH.md](LAUNCH.md) before contributing or reporting sensitive issues. Product
comparison notes live in [docs/comparison.md](docs/comparison.md).

## Screenshots

Screenshots and demo GIFs are planned before the first broad public launch. The capture
checklist lives in [docs/screenshots.md](docs/screenshots.md).

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

After installing CloudSaver as a package, you can also run:

```bash
cloudsaver-web
```

Then open:

```text
http://127.0.0.1:8765
```

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
