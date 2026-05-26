export type ProviderCapabilityState = 'supported' | 'partial' | 'planned' | 'unsupported'

export interface ProviderCapability {
  key: string
  label: string
  maturity: 'production' | 'preview' | 'planned'
  scan: ProviderCapabilityState
  quota: ProviderCapabilityState
  duplicates: ProviderCapabilityState
  cleanup: ProviderCapabilityState
  restore: ProviderCapabilityState
  notes: string
}

export const PROVIDER_CAPABILITIES: ProviderCapability[] = [
  {
    key: 'local',
    label: 'Local folders and mounted drives',
    maturity: 'production',
    scan: 'supported',
    quota: 'unsupported',
    duplicates: 'supported',
    cleanup: 'supported',
    restore: 'supported',
    notes: 'Core local-first workflow with reversible review-folder moves.',
  },
  {
    key: 'icloud',
    label: 'iCloud Drive synced folder',
    maturity: 'preview',
    scan: 'partial',
    quota: 'unsupported',
    duplicates: 'partial',
    cleanup: 'partial',
    restore: 'partial',
    notes: 'Scans local sync path; iCloud-only state handling depends on platform metadata.',
  },
  {
    key: 'google_drive',
    label: 'Google Drive direct account',
    maturity: 'preview',
    scan: 'partial',
    quota: 'partial',
    duplicates: 'partial',
    cleanup: 'partial',
    restore: 'planned',
    notes: 'Remote metadata adapter exists; UI routing and token refresh need production hardening.',
  },
  {
    key: 'dropbox',
    label: 'Dropbox',
    maturity: 'planned',
    scan: 'planned',
    quota: 'planned',
    duplicates: 'planned',
    cleanup: 'planned',
    restore: 'planned',
    notes: 'Only local synced-folder detection exists today.',
  },
  {
    key: 'onedrive',
    label: 'OneDrive',
    maturity: 'planned',
    scan: 'planned',
    quota: 'planned',
    duplicates: 'planned',
    cleanup: 'planned',
    restore: 'planned',
    notes: 'Only local synced-folder detection exists today.',
  },
]
