import { create } from 'zustand'

export type ActiveView = 'overview' | 'sources' | 'duplicates' | 'map' | 'cleanup' | 'settings'

export interface Source {
  id: string
  type: 'local' | 'google_drive' | 'icloud' | 'gdrive_local'
  label: string
  path?: string
  driveAccountEmail?: string
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

interface AppStore {
  activeView: ActiveView
  sidecarPort: number | null
  sidecarReady: boolean
  sources: Source[]
  scanJobs: Record<string, ScanJob>
  scanResults: Record<string, ScanResult>
  duplicateGroups: DuplicateGroup[]
  crossSourceGroups: CrossSourceGroup[]
  reviewBatches: ReviewBatch[]
  commandPaletteOpen: boolean
  theme: 'system' | 'light' | 'dark'

  setView: (view: ActiveView) => void
  setSidecarPort: (port: number) => void
  setCommandPaletteOpen: (open: boolean) => void
  addSource: (source: Source) => void
  removeSource: (id: string) => void
  updateScanJob: (id: string, updates: Partial<ScanJob>) => void
  setScanResult: (sourceId: string, result: ScanResult) => void
  setDuplicateGroups: (groups: DuplicateGroup[]) => void
  setCrossSourceGroups: (groups: CrossSourceGroup[]) => void
  addReviewBatch: (batch: ReviewBatch) => void
  setTheme: (theme: AppStore['theme']) => void
}

export const useStore = create<AppStore>((set) => ({
  activeView: 'overview',
  sidecarPort: null,
  sidecarReady: false,
  sources: [],
  scanJobs: {},
  scanResults: {},
  duplicateGroups: [],
  crossSourceGroups: [],
  reviewBatches: [],
  commandPaletteOpen: false,
  theme: 'system',

  setView: (activeView) => set({ activeView }),
  setSidecarPort: (sidecarPort) => set({ sidecarPort, sidecarReady: true }),
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
  addSource: (source) =>
    set((state) => ({
      sources: state.sources.some((existing) => existing.id === source.id)
        ? state.sources
        : [...state.sources, source],
    })),
  removeSource: (id) =>
    set((state) => ({ sources: state.sources.filter((source) => source.id !== id) })),
  updateScanJob: (id, updates) =>
    set((state) => ({
      scanJobs: {
        ...state.scanJobs,
        [id]: {
          ...state.scanJobs[id],
          id,
          sourceId: updates.sourceId ?? state.scanJobs[id]?.sourceId ?? '',
          status: updates.status ?? state.scanJobs[id]?.status ?? 'queued',
          stage: updates.stage ?? state.scanJobs[id]?.stage ?? 'Waiting',
          filesScanned: updates.filesScanned ?? state.scanJobs[id]?.filesScanned ?? 0,
          currentPath: updates.currentPath ?? state.scanJobs[id]?.currentPath ?? '',
          ...updates,
        },
      },
    })),
  setScanResult: (sourceId, result) =>
    set((state) => ({ scanResults: { ...state.scanResults, [sourceId]: result } })),
  setDuplicateGroups: (duplicateGroups) => set({ duplicateGroups }),
  setCrossSourceGroups: (crossSourceGroups) => set({ crossSourceGroups }),
  addReviewBatch: (batch) =>
    set((state) => ({ reviewBatches: [batch, ...state.reviewBatches] })),
  setTheme: (theme) => set({ theme }),
}))
