# Preview Release Readiness

CloudSaver should ship the first public preview only when the core local cleanup loop is
credible, privacy claims match implementation, and limitations are visible before users
trust the app with real folders.

## Preview Positioning

Target user:

- Creative professionals and small teams with large local or cloud-synced media folders.
- Privacy-conscious users who want a local-first alternative to hosted cleanup tools.
- Open-source users comfortable with a source-first preview.

Promise:

> Scan a local or mounted folder, understand storage usage, review duplicate candidates,
> move selected files into a reversible review folder, and export local reports without
> uploading file names, paths, or contents.

Non-promise:

- No direct cloud-provider API scanning.
- No hosted dashboard.
- No automatic deletion.
- No guaranteed recovery if the user manually deletes reviewed files outside CloudSaver.
- No production support SLA unless a paid support agreement exists.

## Go/No-Go Checklist

### Product

- First-run onboarding leads users to a local folder scan without requiring docs.
- Scan progress, skipped files, permission errors, and completion state are understandable.
- Overview metrics distinguish total storage, included storage, recoverable estimates, and
  review-only files.
- Duplicate review shows verification status, confidence, and a recommended copy to keep.
- Review-folder moves always write a manifest and can be restored through the UI.
- Exclusions and protected folders prevent obvious unsafe system/app cleanup workflows.
- Pro, Business, AI, and payment surfaces are either hidden, marked preview, or fully
  backed by working endpoints.

### Trust

- `README.md`, `PRIVACY.md`, `ROADMAP.md`, and in-app settings describe the same behavior.
- Optional network paths are documented with default state, data sent, and opt-out path.
- `CLOUDSAVER_HOME` controls history, cache, reports, reduced copies, diagnostics, license
  state, and team state.
- Local diagnostics never store file names, paths, email addresses, or IP addresses.
- The source release includes checksums.
- Desktop artifacts are clearly labeled unsigned until signing is configured.

### Engineering

- `python3 -m pytest` passes locally.
- `npm run check:js` passes locally.
- `npm run test:e2e` passes on Chromium.
- `./scripts/release-smoke.sh` passes.
- CI is green on `main`.
- Release workflow can publish source archives, wheels, and `SHA256SUMS`.
- Desktop build workflow either passes or preview notes explicitly say desktop artifacts are
  experimental.

### Launch Assets

- README includes at least three current screenshots:
  - first-run or scan controls
  - dashboard summary
  - duplicate review or review queue
- Release notes include known limitations.
- `docs/screenshots.md` has been completed with actual asset paths.
- A short demo script exists for a maintainer to record a scan/review/restore flow.

## Known Limitations Template

Use this block in the first preview release notes and update it before tagging:

```text
Known limitations:
- Preview builds are unsigned unless the artifact name explicitly says signed.
- Direct Google Drive, iCloud, Dropbox, OneDrive, and S3 APIs are not supported. Scan the
  local synced or mounted folder instead.
- Similar-image detection requires optional image hashing dependencies.
- Video/audio savings are estimates and require ffprobe for media metadata.
- CloudSaver moves files only to a local review folder; it does not permanently delete
  files.
- AI Advisor and Business workspace features are preview-gated and optional.
```

## Pilot Metrics

Track these manually for preview pilots before considering paid launch:

- Installs attempted.
- Installs completed.
- First scans completed.
- Scan failures and reason.
- Total bytes scanned.
- Estimated recoverable bytes.
- Duplicate groups reviewed.
- Files moved to review.
- Restores completed.
- Reports exported.
- Repeat scans within 30 days.
- Sponsors, paid-build interest, or support inquiries.

## Pilot Interview Questions

- What folder did you scan first, and why?
- Did you trust the app before selecting files to move?
- Which screen made the cleanup decision easiest?
- Which warning, label, or action felt unclear?
- Did the report help you avoid a storage upgrade or cleanup manually?
- Would you pay for signed builds, professional reports, or support?

## Exit Criteria For Paid Convenience Work

Do not lead with paid Pro conversion until preview pilots show:

- At least 50 completed scans from external users.
- At least 10 repeat users or teams.
- At least 5 users who explicitly ask for signed builds, reports, or support.
- No unresolved safety issue in review/restore.
- Privacy docs and app behavior remain aligned.
- `docs/privacy-architecture.md` and `docs/safety-model.md` are current.
