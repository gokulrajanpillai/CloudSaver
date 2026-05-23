import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'
import type {
  CrossSourceGroup,
  DuplicateGroup,
  ReviewBatch,
  ScanJob,
  ScanResult,
  Source,
  VisualGroup,
} from '@/types'

export type ActiveView = 'overview' | 'sources' | 'duplicates' | 'map' | 'cleanup' | 'settings'
export type { CrossSourceGroup, DuplicateGroup, ReviewBatch, ScanJob, ScanResult, Source, VisualGroup }

interface AppStore {
  activeView: ActiveView
  sidecarPort: number | null
  sidecarReady: boolean
  sources: Source[]
  scanJobs: Record<string, ScanJob>
  scanResults: Record<string, ScanResult>
  duplicateGroups: DuplicateGroup[]
  crossSourceGroups: CrossSourceGroup[]
  visualGroups: VisualGroup[]
  reviewBatches: ReviewBatch[]
  commandPaletteOpen: boolean
  theme: 'system' | 'light' | 'dark'

  setView: (view: ActiveView) => void
  setSidecarPort: (port: number) => void
  setCommandPaletteOpen: (open: boolean) => void
  addSource: (source: Source) => void
  updateSource: (id: string, updates: Partial<Source>) => void
  removeSource: (id: string) => void
  updateScanJob: (id: string, updates: Partial<ScanJob>) => void
  setScanResult: (sourceId: string, result: ScanResult) => void
  setDuplicateGroups: (groups: DuplicateGroup[]) => void
  setCrossSourceGroups: (groups: CrossSourceGroup[]) => void
  setVisualGroups: (groups: VisualGroup[]) => void
  addReviewBatch: (batch: ReviewBatch) => void
  removeReviewBatch: (id: string) => void
  setTheme: (theme: AppStore['theme']) => void
}

export const useStore = create<AppStore>()(
  persist(
    (set) => ({
  activeView: 'overview',
  sidecarPort: null,
  sidecarReady: false,
  sources: [],
  scanJobs: {},
  scanResults: {},
  duplicateGroups: [],
  crossSourceGroups: [],
  visualGroups: [],
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
  updateSource: (id, updates) =>
    set((state) => ({
      sources: state.sources.map((source) =>
        source.id === id ? { ...source, ...updates } : source,
      ),
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
  setVisualGroups: (visualGroups) => set({ visualGroups }),
  addReviewBatch: (batch) =>
    set((state) => ({ reviewBatches: [batch, ...state.reviewBatches] })),
  removeReviewBatch: (id) =>
    set((state) => ({ reviewBatches: state.reviewBatches.filter((batch) => batch.id !== id) })),
  setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'cloudsaver-app',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        sources: state.sources.map(({ accessToken, ...source }) => source),
        theme: state.theme,
      }),
    },
  ),
)
