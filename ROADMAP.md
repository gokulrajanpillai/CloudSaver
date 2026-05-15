# Roadmap

CloudSaver's roadmap is organized around one principle: keep the core local-first and open
source while making the product easier to install, trust, sponsor, and use.

The detailed phase-by-phase implementation and revenue rollout lives in
[docs/revenue-rollout-plan.md](docs/revenue-rollout-plan.md). This roadmap is the short
operating summary.

## Now

- Make repository claims match shipped automation, especially CI and release workflows.
- Centralize app-data paths so history, cache, reports, and review folders respect
  `CLOUDSAVER_HOME`.
- Fix local tests so they never write to a user's default `~/.cloudsaver` database.
- Improve dashboard clarity, onboarding, and screenshots for a preview release.
- Keep cleanup safe by default with protected folders, quarantine, and restore flows.
- Add sponsorship metadata and value-triggered, non-blocking sponsor prompts.

## Next

- Publish a source-first preview GitHub Release and validate it with the release smoke
  checklist.
- Split `cloudsaver.core` into scan, audit, duplicates, media, quarantine, reports, and
  path/config modules.
- Add richer treemap drill-down, folder ranking, file actions, and platform reveal support.
- Add exclusions, protected folders, and cleanup policy presets.
- Improve duplicate review with verification confidence, keep-copy recommendations, and
  safer batch selection.
- Complete the launch checklist in [LAUNCH.md](LAUNCH.md).

## Later

- Add signed convenience builds for macOS and Windows while keeping source releases free.
- Publish package-manager manifests for Homebrew, Winget, Scoop, and Flatpak.
- Add release checksums, SBOMs, and release provenance.
- Sell optional commercial support, business report templates, and professional
  implementation help.
- Add Pro features only after the open-source core is competitive and trusted.
- Validate business/team workflows with early professional users before broad release.

## Monetization Boundary

CloudSaver's core scanner, local dashboard, duplicate review, and safe cleanup primitives
remain open source. Paid convenience can focus on signed builds, store delivery, updates,
support, business templates, optional AI assistance, scheduled audits, and team workflows.

The product should not make the open-source version artificially weak. Revenue should come
from trust, convenience, support, automation, and professional reporting.

Licensing strategy is documented in [docs/licensing-strategy.md](docs/licensing-strategy.md).

## Out Of Scope For Now

- Hosted accounts.
- Required telemetry.
- Cloud-provider API integrations.
- Silent deletion.
- Uploading file names, paths, or contents by default.
