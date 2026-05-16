# Privacy

CloudSaver is designed as a local-first storage audit tool.

Detailed design notes live in [docs/privacy-architecture.md](docs/privacy-architecture.md)
and cleanup safety rules live in [docs/safety-model.md](docs/safety-model.md).

## What CloudSaver Scans

When you choose a folder, CloudSaver reads local filesystem metadata such as file name,
path, size, parent folder, and inferred MIME type. For image reduction, CloudSaver opens
only the selected image files and writes reduced copies to the configured output folder.

## What Stays Local

CloudSaver does not upload file contents, file names, file paths, scan results, or usage
events to a hosted CloudSaver service during the local scan and cleanup workflow.

CloudSaver does keep local app data on your machine, including scan history, reduced image
copies, review manifests, optional license state, and a local diagnostics database. These
files are stored under the CloudSaver app data directory unless a specific output location
is configured.

## Optional Network Features

CloudSaver's core workflow does not require an account or cloud-provider credentials. Some
optional features can contact external services when they are configured or explicitly used.

| Feature | Default state | Data sent | How to disable or avoid |
| --- | --- | --- | --- |
| Update checks | Local app can query release metadata when enabled by the packaged build | App version and standard HTTP request metadata | Do not enable update checks or use source installs |
| Stripe checkout | Only used when buying a paid convenience or Pro plan | Plan id, optional email, and Stripe payment metadata | Do not start checkout |
| License activation | Only used after entering a license key or returning from checkout | License key and optional email are stored locally; checkout delivery uses Stripe session metadata | Do not activate a license |
| AI Storage Advisor | Requires Pro and an AI API key | Redacted storage summaries: counts, sizes, categories, codec patterns, and trends. File names and paths are excluded. | Do not configure the AI API key or do not run advisor analysis |
| Team workspace | Requires Business tier | Redacted audit summaries shared locally through the workspace database; root paths are redacted in shared audits | Do not create or join a team workspace |

If a future hosted CloudSaver service is added, it must be documented here before release.

## Local Diagnostics

CloudSaver records local-only diagnostic events such as completed scans, feature usage
counts, and coarse saved-space estimates. The local diagnostics database does not store file
names, paths, user ids, IP addresses, or email addresses.

Set `CLOUDSAVER_NO_ANALYTICS=1` before starting CloudSaver to disable local diagnostics
writes.

## Output Files

CloudSaver may write reports and reduced image copies to the local `output/` folder unless
configured otherwise. Review generated reports before sharing them because they can contain
local file names and paths.

## Credentials

CloudSaver does not require cloud-provider credentials for the local and mounted-folder
workflow. Do not commit credentials, tokens, private reports, or generated scan output.

## Future Changes

New networked features should be documented here, disabled by default where practical, and
reviewed for privacy impact before release.
