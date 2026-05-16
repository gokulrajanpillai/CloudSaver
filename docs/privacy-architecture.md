# Privacy Architecture

CloudSaver is designed around a local-first storage audit and cleanup workflow. The core
workflow should remain useful without accounts, hosted dashboards, cloud-provider
credentials, or file uploads.

## Local Scan Boundary

When a user chooses a folder, CloudSaver reads local filesystem metadata and selected file
contents only when needed for a local operation.

Read during scan:

- File names.
- Local paths.
- File sizes.
- Parent folders.
- File timestamps.
- Inferred MIME types.
- Optional media metadata when `ffprobe` is available.

Read during duplicate verification:

- Candidate duplicate file contents are hashed locally with SHA-256.
- Hashes are used for verification and cache acceleration.

Read during image-copy workflows:

- Selected image files are opened locally.
- Reduced or converted copies are written to the configured output directory.
- Originals are not modified by the image-copy workflow.

## Local Storage

CloudSaver stores local app data under `CLOUDSAVER_HOME` when set, otherwise under the
default CloudSaver app-data directory.

Local app data can include:

- Scan history database.
- File hash/cache database.
- Local diagnostics database.
- Reduced image copies.
- Generated reports.
- Review manifests.
- Optional license state.
- Optional team workspace state.

Generated reports may contain local file names and paths. Review them before sharing.

## Optional Network Paths

The local scan and cleanup workflow does not upload file contents, file names, paths, scan
results, or usage events to a hosted CloudSaver service.

Optional network paths:

| Feature | When used | Data boundary |
| --- | --- | --- |
| Update checks | When enabled by a packaged build | App version and standard HTTP request metadata |
| Stripe checkout | When the user starts checkout | Plan id, optional email, and Stripe payment metadata |
| License delivery | After successful checkout or manual activation | License key and optional email are stored locally; checkout delivery uses Stripe session metadata |
| AI Storage Advisor | Only when Pro, API key, and advisor action are configured | Redacted summaries: counts, sizes, categories, codec patterns, and trends. File names and paths are excluded. |
| Team workspace | Only when Business workspace actions are used | Redacted audit summaries; shared audit root paths are redacted |

## Diagnostics

Local diagnostics are stored in a local SQLite database. They are intended to help users and
maintainers understand feature usage and coarse outcomes without storing private paths.

Allowed diagnostics:

- Event names.
- Feature names.
- Counts.
- Coarse saved-space estimates.
- Error types.

Not allowed in diagnostics:

- File names.
- File paths.
- Email addresses.
- IP addresses.
- User documents or file contents.

Set `CLOUDSAVER_NO_ANALYTICS=1` before starting CloudSaver to disable local diagnostics
writes.

## Privacy Review Checklist

Before adding a new feature, answer:

- Does it read file contents?
- Does it write a report, cache, or manifest?
- Does it send any data over the network?
- Can it run without accounts or credentials?
- Does `PRIVACY.md` describe the data path?
- Can the user disable or avoid the feature?
- Are file names and paths redacted before sharing?
