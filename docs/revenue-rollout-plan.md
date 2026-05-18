# CloudSaver Revenue And Product Rollout Plan

CloudSaver stays open source first. Revenue should fund trust, maintenance, packaging, and
professional support without weakening the local-first core product.

## Guiding Boundary

The open-source core should remain useful enough that privacy-conscious users can inspect,
build, and trust the product without paying.

Keep open:

- Local scan engine
- Local web dashboard
- Storage map
- Exact duplicate detection and verification
- Safe review folder and restore manifests
- JSON, CSV, and HTML reports
- CLI and source-install workflow

Paid value can focus on:

- Signed macOS and Windows builds
- Store distribution
- Auto-update convenience
- Priority support
- Business reports
- Policy presets for professional users
- Optional AI and team workflows after the core is stable

## Phase 0: Codebase Trust Baseline

Goal: make the repository match the public product claims.

Engineering changes:

- Add real GitHub Actions workflows for Python tests, frontend checks, Playwright tests,
  packaging smoke checks, and release artifacts.
- Centralize app-data paths so `CLOUDSAVER_HOME` controls history, cache, reports, reduced
  image copies, and review folders consistently.
- Fix tests that write to the user's default `~/.cloudsaver` database.
- Add linting and formatting gates with a documented local command.
- Add dependency and secret scanning to CI.
- Update privacy documentation for every optional network path: update checks, payments,
  GitHub marketing metadata, and AI advisor calls.

Revenue work:

- Add GitHub Sponsors funding metadata.
- Make sponsor calls visible in README and non-blocking in the app.
- Keep all prompts value-triggered, such as after a scan or report export.

Exit criteria:

- Local tests pass from a clean checkout.
- CI is green on pull requests.
- README claims match shipped automation.
- No runtime path writes outside the configured app-data home except selected scan targets.

## Phase 1: Preview Release

Goal: release a credible open-source preview that earns users and sponsors.

Engineering changes:

- Ship a source-first preview release with checksums and clear platform notes.
- Add screenshots and a short demo flow to README.
- Polish onboarding around three promises: local scan, review before moving, restore support.
- Improve scan status, error messages, and empty states.
- Keep Pro, Business, payments, advisor, and team workflows clearly labeled as preview if
  they remain visible.

Revenue work:

- Publish sponsor tiers tied to concrete work: signed builds, accessibility, packaging, and
  duplicate review polish.
- Add a "fund this milestone" section to roadmap issues.
- Start collecting early commercial-support interest without selling unsupported guarantees.

Exit criteria:

- `v1.1.0` can be installed and tested by external users.
- Sponsor links are present but not intrusive.
- Preview limitations are explicit.
- The product can be recommended as a safe local audit tool.

## Phase 2: Competitive Open-Source Core

Goal: compete on the actual cleanup workflow before charging for advanced value.

Engineering changes:

- Split `cloudsaver.core` into scan, audit, duplicates, media, quarantine, reports, and
  path/config modules.
- Add protected folders, exclusions, and cleanup policy presets.
- Harden quarantine and restore as a transaction-like workflow with manifest-first writes,
  partial-failure handling, and rollback guidance.
- Improve storage map drill-down, folder ranking, category legend, and file actions.
- Improve duplicate review with confidence labels, hash status, "keep best copy" selection,
  and reference-folder support.
- Add accessibility coverage for keyboard navigation, dialogs, focus management, and color
  contrast.

Revenue work:

- Keep the full local cleanup loop free.
- Ask for sponsorship after high-value moments: large recoverable estimate, successful
  restore, or useful report export.
- Publish public metrics on funded work, such as "sponsors funded Windows signing."

Exit criteria:

- A user can safely scan, understand, review, move, and restore files without reading docs.
- Duplicate review is safer and clearer than a naive file list.
- The open-source version is credible on its own.

## Phase 3: Paid Convenience Builds

Goal: create reliable revenue without closing the core.

Engineering changes:

- Add signed and notarized macOS builds.
- Add signed Windows builds.
- Add release checksums, SBOM, and release provenance.
- Validate Homebrew, Winget, Scoop, and Flatpak templates.
- Add a simple update channel for paid convenience builds, with source builds still possible.

Revenue work:

- Sell paid signed builds through one low-friction channel first.
- Keep GitHub source releases free.
- Price for convenience, not scarcity. Start with a simple one-time consumer price and a
  higher commercial-support option.
- Offer invoices and support terms for professional users.

Exit criteria:

- Users can pay for a build because it is easier and more trusted, not because the open
  source version is crippled.
- Release artifacts are reproducible enough to inspect and verify.
- Support load and refund policy are documented.

## Phase 4: Pro Features

Goal: add paid product value after the core is trusted.

Engineering changes:

- Define clear feature gates in one module and expose license state consistently to the UI.
- Keep basic safety, restore, reports, and exact duplicates free.
- Add advanced features only where they create professional value:
  - AI cleanup advisor
  - Perceptual duplicate review
  - Scheduled local audits
  - Advanced media savings analysis
  - Redacted business reports
- Add offline-friendly license handling where practical.

Revenue work:

- Offer Pro as a convenience and intelligence tier, not as the only useful product.
- Keep payment processing optional for source users and documented for packaged builds.
- Avoid subscriptions until recurring value is clear. Prefer one-time or annual support
  pricing first.

Exit criteria:

- Paying users get measurable time savings or professional reporting value.
- Non-paying users still get a complete local storage audit and safe cleanup workflow.
- License failures never block access to user data or restore functions.

## Phase 5: Business And Team Workflows

Goal: support small teams and professional users without turning CloudSaver into a hosted
data product.

Engineering changes:

- Add redaction defaults for shared audit summaries.
- Add business report templates with before/after savings, category trends, and reviewed
  cleanup actions.
- Add admin policies for protected folders, excluded paths, and scheduled local audits.
- Add import/export for policy presets.
- Keep team sharing explicit, local-first, and privacy-reviewed before enabling by default.

Revenue work:

- Sell commercial support, deployment help, and reporting templates.
- Offer Business annual plans only when support processes exist.
- Avoid hosted dashboards unless a separate privacy and security review approves them.

Exit criteria:

- A small business can run CloudSaver safely with documented policies.
- Reports can be shared without exposing unnecessary private paths.
- Commercial support terms match actual maintainer capacity.

## Phase 6: Scale And Governance

Goal: make revenue sustainable while protecting the open-source project.

Engineering changes:

- Add a public security architecture document.
- Publish SBOMs for release builds.
- Maintain a release checklist and support matrix.
- Track roadmap issues by sponsor-funded, community, paid-build, and commercial-support
  labels.
- Add contributor onboarding for privacy-sensitive code paths.

Revenue work:

- Review sponsor conversion, paid-build sales, support load, and refund reasons each
  release cycle.
- Keep a public funding ledger or summary if sponsor volume grows.
- Revisit license strategy only if commercial extraction becomes a real problem.

Exit criteria:

- Revenue funds visible maintenance work.
- Community contributors can still participate without entering proprietary-only areas.
- The project can explain exactly what is free, what is paid, and why.
