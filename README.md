# CloudSaver

Find storage you're not using. Free and open source, local-first.

[![CI](https://github.com/gokulrajanpillai/CloudSaver/workflows/CI/badge.svg)](https://github.com/gokulrajanpillai/CloudSaver/actions)
[![License](https://img.shields.io/github/license/gokulrajanpillai/CloudSaver)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.1.0-blue)](CHANGELOG.md)

CloudSaver scans local drives, synced cloud folders (Google Drive, iCloud, Dropbox,
OneDrive), external drives, and NAS mounts. It finds duplicate files, oversized media,
cold archives, and storage growth trends — then gives you a safe, reversible cleanup
workflow backed by restore manifests.

**Files stay on your machine.** CloudSaver never uploads file contents, filenames, or paths.

Runs on macOS, Linux, and Windows. Tested across Python 3.10–3.12.

---

## What it finds

- **Duplicate files** — exact and perceptual matches, with a recommended copy to keep
- **Oversized media** — large images and videos that can be reduced without losing originals
- **Cold archives** — files untouched for months taking up active storage space
- **Storage growth** — month-over-month trend so you can act before hitting a limit
- **Cost estimate** — rough monthly cloud storage cost avoidable from recoverable space

---

## Screenshots

<!-- Add screenshots after running: python3 scripts/create-demo-fixture.py -->

| Scan & Dashboard | Duplicate Review | Storage Map |
|---|---|---|
| ![Dashboard](docs/assets/dashboard-summary.png) | ![Duplicates](docs/assets/duplicate-review.png) | ![Map](docs/assets/storage-map.png) |

---

## Install

**From source (all platforms):**

```bash
git clone https://github.com/gokulrajanpillai/CloudSaver.git
cd CloudSaver
python3 -m pip install -e .
python3 -m cloudsaver.web_server
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765).

**With optional features:**

```bash
# AI Advisor (requires ANTHROPIC_API_KEY)
python3 -m pip install -e ".[advisor]"

# Better image duplicate detection
python3 -m pip install -e ".[image_extras]"
```

See [docs/install.md](docs/install.md) for platform-specific notes and desktop builds.

---

## Quick start

```bash
# Start the web UI
python3 -m cloudsaver.web_server

# Or use the startup script
./scripts/start-cloudsaver.sh       # macOS / Linux
.\scripts\start-cloudsaver.ps1      # Windows PowerShell
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765), choose a folder, and click **Start scan**.

To scan your synced Google Drive or iCloud folder, point CloudSaver at the local sync path:

```
/Users/you/Library/CloudStorage/GoogleDrive-you@example.com/My Drive
/Users/you/Library/Mobile Documents/com~apple~CloudDocs
/Volumes/SharedDrive
```

---

## Features

**Scan & analyze**
- Scan any local or mounted folder
- Live scan progress with file counts and size totals
- Storage treemap with folder drill-down
- File categorization (images, video, audio, documents, archives)
- Month-over-month storage growth trend

**Duplicate review**
- Find exact duplicates via SHA-256 verification
- Find perceptual image duplicates (requires `image_extras`)
- Recommended keep copy with confidence labels
- Move duplicate extras to a reversible review folder

**Safe cleanup**
- Files are never deleted — moved to `.cloudsaver-review` with a restore manifest
- Restore individual files or entire batches through the UI
- Protected paths prevent accidental system folder scans

**Exports & reports**
- Download JSON or CSV file reports from the web UI
- Generate an HTML storage dashboard
- Business report templates for team cleanup reviews

**Optional Pro features** (requires license key)
- AI Storage Advisor powered by Claude — analyzes anonymous storage stats and recommends
  ranked cleanup actions with estimated cost savings
- Business tier: team workspaces, shared audit summaries, scheduled scans

---

## Privacy

The local scan and cleanup workflow does not upload file contents, filenames, file paths,
scan results, or usage events to any remote service.

Optional network paths (all opt-in):

| Feature | Data sent |
| --- | --- |
| Update checks | App version only |
| Stripe checkout | Plan ID and payment metadata |
| AI Advisor | Redacted summaries: counts, sizes, categories — no paths or filenames |
| Team workspace | Redacted audit summaries — root paths are stripped |

Set `CLOUDSAVER_NO_ANALYTICS=1` to disable local diagnostics writes.

See [PRIVACY.md](PRIVACY.md) and [docs/privacy-architecture.md](docs/privacy-architecture.md)
for the full data boundary.

---

## Development

```bash
# Install with dev dependencies
python3 -m pip install -e ".[dev]"

# Run Python tests
python3 -m pytest

# Run frontend checks and browser tests
npm ci
npx playwright install chromium
npm run check:js
npm run test:e2e

# Startup smoke check
./scripts/start-cloudsaver.sh
curl -fsS http://127.0.0.1:8765/api/health
```

CI runs the Python test matrix (3 OS × 3 Python versions), Playwright browser tests,
package build, and startup smoke check on every push and pull request.

---

## Support

CloudSaver is free and open source. If it helps you avoid a storage upgrade or recover
space, consider supporting development:

- **GitHub Sponsors:** [github.com/sponsors/gokulrajanpillai](https://github.com/sponsors/gokulrajanpillai)
- **Commercial support:** [docs/commercial-support.md](docs/commercial-support.md) — setup help, report interpretation, cleanup planning
- **Issues and roadmap:** [github.com/gokulrajanpillai/CloudSaver/issues](https://github.com/gokulrajanpillai/CloudSaver/issues)

---

See [PRIVACY.md](PRIVACY.md), [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md),
[ROADMAP.md](ROADMAP.md), and [CHANGELOG.md](CHANGELOG.md) for more.
