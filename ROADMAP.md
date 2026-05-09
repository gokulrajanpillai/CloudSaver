# Roadmap

CloudSaver's roadmap is organized around one principle: keep the core local-first and open
source while making the product easier to install, trust, sponsor, and use.

## Now

- Polish the repository for public adoption.
- Improve dashboard clarity and screenshots.
- Stabilize local scan history and report formats.
- Keep cleanup safe by default with quarantine and restore flows.
- Validate GitHub release artifacts across macOS, Windows, and Linux.

## Next

- Restructure the Python package from `src` modules into a `cloudsaver` package.
- Expand the app navigation model with deeper Cleanup and Support views.
- Add richer treemap details, file actions, and platform reveal support.
- Add protected folders, exclusions, and cleanup policy presets.
- Publish a preview GitHub Release and validate it with the release smoke checklist.
- Complete the launch checklist in [LAUNCH.md](LAUNCH.md).

## Later

- Add signed convenience builds for macOS and Windows.
- Publish package-manager manifests for Homebrew, Winget, Scoop, and Flatpak.
- Add optional commercial support and business report templates.
- Validate commercial support packages with early professional users.
- Explore a native desktop shell after the web UI stabilizes.

## Monetization Boundary

CloudSaver's core scanner, local dashboard, duplicate review, and safe cleanup primitives
remain open source. Paid convenience can focus on signed builds, store delivery, updates,
support, and business templates.

Licensing strategy is documented in [docs/licensing-strategy.md](docs/licensing-strategy.md).

## Out Of Scope For Now

- Hosted accounts.
- Required telemetry.
- Cloud-provider API integrations.
- Silent deletion.
- Uploading file names, paths, or contents by default.
