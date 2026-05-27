export const PROVIDER_LIMITATIONS = [
  {
    provider: 'Google Drive',
    limitation: 'Direct account scans are preview-grade; local synced folders remain the safest path.',
  },
  {
    provider: 'iCloud Drive',
    limitation: 'Cloud-only files may be placeholders. Scans can only inspect files available through the local sync path.',
  },
  {
    provider: 'Dropbox',
    limitation: 'Direct API support is planned. Scan the local Dropbox sync folder today.',
  },
  {
    provider: 'OneDrive',
    limitation: 'Direct Microsoft Graph support is planned. Scan the local OneDrive sync folder today.',
  },
  {
    provider: 'S3 and NAS',
    limitation: 'Dedicated connectors are planned. Mounted folders and shares can be scanned as local sources.',
  },
]
