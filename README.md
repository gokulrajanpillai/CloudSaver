# CloudSaver

![CI](https://github.com/gokulrajanpillai/CloudSaver/workflows/CI/badge.svg)

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

## Storage Audit Dashboard

CloudSaver can run a read-only storage audit and generate:

- `output/storage_audit.html`: a browser-friendly dashboard
- `output/storage_audit.json`: the same audit data for downstream processing

The audit summarizes total storage, storage by file category, largest files, largest folders,
duplicate candidates, large files to review, and estimated recoverable space from duplicate
candidates plus image optimization. The web UI also estimates rough monthly cloud storage
cost avoided and can download local JSON or CSV reports.

## Features

- Scan any local or mounted folder
- Use the local web UI to choose a drive or enter a specific path
- Export all file metadata to JSON
- Export files larger than a selected size
- Generate an HTML storage dashboard
- Download JSON and CSV reports from the local web UI
- Find duplicate candidates by file name and size, with SHA-256 verification for readable
  local candidates in the web UI
- Create reduced 1080p copies of large images in `output/reduced`
- Estimate per-file and selected-file size reductions before processing

CloudSaver does not delete files during duplicate scanning. Review the generated audit before
removing files manually.

## Open Source Scope

CloudSaver focuses on local and mounted storage. Direct cloud-provider APIs, user accounts,
hosted dashboards, telemetry, and automatic deletion are intentionally out of scope for now.

See [PRIVACY.md](PRIVACY.md), [CONTRIBUTING.md](CONTRIBUTING.md), and
[SECURITY.md](SECURITY.md) before contributing or reporting sensitive issues.

## Usage

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run the web UI:

```bash
python3 -m src.cloudsaver_web
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
python3 -m src.cloudsaver
```

Or, after package installation:

```bash
cloudsaver
```

When prompted, enter the folder path you want to scan. For example:

```text
/Users/you/Library/CloudStorage/GoogleDrive-you@example.com/My Drive
/Volumes/SharedDrive
/Users/you/Pictures
```
