export type SourceType = 'local' | 'google_drive' | 'icloud' | 'gdrive_local'

export interface Source {
  id: string
  type: SourceType
  label: string
  path?: string
  driveAccountEmail?: string
  accessToken?: string
  quota?: { used: number; total: number }
  lastScanned?: string
  fileCount?: number
  totalBytes?: number
  status: 'idle' | 'scanning' | 'error' | 'ready'
  errorMessage?: string
}

export interface ScanResult {
  rootPath?: string
  sourceId?: string
  quota?: { used: number; total: number; drive_used?: number }
  audit?: Record<string, unknown>
  files: Array<Record<string, unknown>>
}

export interface ScanJob {
  id: string
  sourceId: string
  sourceName?: string
  status: 'queued' | 'scanning' | 'complete' | 'failed'
  stage: string
  filesScanned: number
  currentPath: string
  progress?: number
  result?: ScanResult
  error?: string
}

export interface DuplicateGroup {
  id?: string
  name?: string
  files?: Array<Record<string, unknown>>
  recoverableBytes?: number
}

export interface CrossSourceGroup extends DuplicateGroup {
  confidence?: 'low' | 'medium' | 'high'
}

export interface ReviewBatch {
  id: string
  sourceId: string
  sourceLabel: string
  fileCount: number
  manifestPath: string
  createdAt: string
}
