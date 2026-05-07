# Privacy

CloudSaver is designed as a local-first storage audit tool.

## What CloudSaver Scans

When you choose a folder, CloudSaver reads local filesystem metadata such as file name,
path, size, parent folder, and inferred MIME type. For image reduction, CloudSaver opens
only the selected image files and writes reduced copies to the configured output folder.

## What Stays Local

CloudSaver does not upload file contents, file names, file paths, scan results, or usage
events to a hosted CloudSaver service.

The current project does not include telemetry, accounts, analytics, ads, or remote
licensing.

## Output Files

CloudSaver may write reports and reduced image copies to the local `output/` folder unless
configured otherwise. Review generated reports before sharing them because they can contain
local file names and paths.

## Credentials

CloudSaver does not require cloud-provider credentials for the local and mounted-folder
workflow. Do not commit credentials, tokens, private reports, or generated scan output.

## Future Changes

If optional networked features are ever added, they should be documented here, disabled by
default where practical, and reviewed for privacy impact before release.
