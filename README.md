# CloudSaver

CloudSaver audits and optimizes storage in a local or mounted folder. It works with any
folder your operating system can see, including synced cloud folders, external drives, NAS
mounts, and local directories.

## Storage Audit Dashboard

CloudSaver can run a read-only storage audit and generate:

- `output/storage_audit.html`: a browser-friendly dashboard
- `output/storage_audit.json`: the same audit data for downstream processing

The audit summarizes total storage, storage by file category, largest files, largest folders,
duplicate candidates, large files to review, and estimated recoverable space from duplicate
cleanup plus image optimization.

## Features

- Scan any local or mounted folder
- Export all file metadata to JSON
- Export files larger than a selected size
- Generate an HTML storage dashboard
- Find duplicate candidates by file name and size
- Create reduced 1080p copies of large images in `output/reduced`

CloudSaver does not delete files during duplicate scanning. Review the generated audit before
removing files manually.

## Usage

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run the CLI:

```bash
python3 -m src.cloudsaver
```

When prompted, enter the folder path you want to scan. For example:

```text
/Users/you/Library/CloudStorage/GoogleDrive-you@example.com/My Drive
/Volumes/SharedDrive
/Users/you/Pictures
```
