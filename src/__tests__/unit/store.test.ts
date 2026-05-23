import { beforeEach, describe, expect, it } from 'vitest'
import { useStore } from '@/store'
import type { Source, ScanJob } from '@/store'

const makeSource = (overrides: Partial<Source> = {}): Source => ({
  id: 'src-1',
  type: 'local',
  label: 'Downloads',
  path: '/Users/me/Downloads',
  status: 'idle',
  ...overrides,
})

const makeJob = (overrides: Partial<ScanJob> = {}): ScanJob => ({
  id: 'job-1',
  sourceId: 'src-1',
  sourceName: 'Downloads',
  status: 'queued',
  stage: 'Waiting',
  filesScanned: 0,
  currentPath: '',
  ...overrides,
})

beforeEach(() => {
  useStore.setState({
    sources: [],
    scanJobs: {},
    scanResults: {},
    duplicateGroups: [],
    crossSourceGroups: [],
    visualGroups: [],
    reviewBatches: [],
  })
})

describe('sources', () => {
  it('addSource adds a source', () => {
    useStore.getState().addSource(makeSource())
    expect(useStore.getState().sources).toHaveLength(1)
  })

  it('addSource ignores duplicate id', () => {
    const src = makeSource()
    useStore.getState().addSource(src)
    useStore.getState().addSource(src)
    expect(useStore.getState().sources).toHaveLength(1)
  })

  it('updateSource merges partial fields', () => {
    useStore.getState().addSource(makeSource({ status: 'idle' }))
    useStore.getState().updateSource('src-1', { status: 'scanning', fileCount: 42 })
    const src = useStore.getState().sources[0]
    expect(src.status).toBe('scanning')
    expect(src.fileCount).toBe(42)
    expect(src.label).toBe('Downloads') // untouched
  })

  it('updateSource leaves other sources untouched', () => {
    useStore.getState().addSource(makeSource({ id: 'src-1' }))
    useStore.getState().addSource(makeSource({ id: 'src-2', label: 'Desktop' }))
    useStore.getState().updateSource('src-1', { status: 'ready' })
    expect(useStore.getState().sources.find((s) => s.id === 'src-2')?.label).toBe('Desktop')
  })

  it('removeSource removes by id', () => {
    useStore.getState().addSource(makeSource())
    useStore.getState().removeSource('src-1')
    expect(useStore.getState().sources).toHaveLength(0)
  })

  it('removeSource is no-op for unknown id', () => {
    useStore.getState().addSource(makeSource())
    useStore.getState().removeSource('unknown-id')
    expect(useStore.getState().sources).toHaveLength(1)
  })
})

describe('scanJobs', () => {
  it('updateScanJob creates entry with defaults', () => {
    useStore.getState().updateScanJob('job-1', { sourceId: 'src-1', status: 'queued', stage: 'Waiting', filesScanned: 0, currentPath: '' })
    const job = useStore.getState().scanJobs['job-1']
    expect(job).toBeDefined()
    expect(job.status).toBe('queued')
  })

  it('updateScanJob merges into existing entry', () => {
    useStore.getState().updateScanJob('job-1', makeJob())
    useStore.getState().updateScanJob('job-1', { filesScanned: 99, progress: 0.5 })
    const job = useStore.getState().scanJobs['job-1']
    expect(job.filesScanned).toBe(99)
    expect(job.progress).toBe(0.5)
    expect(job.sourceId).toBe('src-1') // preserved
  })

  it('updateScanJob preserves sourceId from existing when update omits it', () => {
    useStore.getState().updateScanJob('job-1', makeJob({ sourceId: 'src-1' }))
    useStore.getState().updateScanJob('job-1', { filesScanned: 10 })
    expect(useStore.getState().scanJobs['job-1'].sourceId).toBe('src-1')
  })
})

describe('scanResults', () => {
  it('setScanResult stores by sourceId', () => {
    const result = { sourceId: 'src-1', files: [], audit: {} }
    useStore.getState().setScanResult('src-1', result)
    expect(useStore.getState().scanResults['src-1']).toEqual(result)
  })

  it('setScanResult overwrites existing result for same sourceId', () => {
    useStore.getState().setScanResult('src-1', { sourceId: 'src-1', files: [], audit: {} })
    useStore.getState().setScanResult('src-1', { sourceId: 'src-1', files: [{ name: 'a' }], audit: {} })
    expect(useStore.getState().scanResults['src-1'].files).toHaveLength(1)
  })
})

describe('duplicate groups', () => {
  it('setDuplicateGroups replaces full array', () => {
    useStore.getState().setDuplicateGroups([{ id: 'dup-1', recoverableBytes: 100 }])
    expect(useStore.getState().duplicateGroups).toHaveLength(1)
    useStore.getState().setDuplicateGroups([])
    expect(useStore.getState().duplicateGroups).toHaveLength(0)
  })

  it('setCrossSourceGroups replaces full array', () => {
    useStore.getState().setCrossSourceGroups([{ id: 'cross-1', recoverableBytes: 200 }])
    expect(useStore.getState().crossSourceGroups).toHaveLength(1)
    useStore.getState().setCrossSourceGroups([])
    expect(useStore.getState().crossSourceGroups).toHaveLength(0)
  })

  it('setVisualGroups replaces full array', () => {
    useStore.getState().setVisualGroups([{ id: 'vis-1', recoverableBytes: 300, similarity: 95, files: [] }])
    expect(useStore.getState().visualGroups).toHaveLength(1)
    useStore.getState().setVisualGroups([])
    expect(useStore.getState().visualGroups).toHaveLength(0)
  })
})

describe('navigation', () => {
  it('setView updates activeView', () => {
    useStore.getState().setView('sources')
    expect(useStore.getState().activeView).toBe('sources')
  })

  it('setView accepts all valid views', () => {
    const views = ['overview', 'sources', 'duplicates', 'map', 'cleanup', 'settings'] as const
    for (const view of views) {
      useStore.getState().setView(view)
      expect(useStore.getState().activeView).toBe(view)
    }
  })
})

describe('sidecar', () => {
  it('setSidecarPort sets port and marks sidecarReady=true', () => {
    useStore.setState({ sidecarPort: null, sidecarReady: false })
    useStore.getState().setSidecarPort(8765)
    expect(useStore.getState().sidecarPort).toBe(8765)
    expect(useStore.getState().sidecarReady).toBe(true)
  })
})

describe('reviewBatches', () => {
  it('addReviewBatch prepends to list', () => {
    useStore.getState().addReviewBatch({ id: 'rb-1', sourceId: 'src-1', sourceLabel: 'Downloads', fileCount: 3, manifestPath: '/tmp/manifest.json', createdAt: new Date().toISOString() })
    useStore.getState().addReviewBatch({ id: 'rb-2', sourceId: 'src-1', sourceLabel: 'Downloads', fileCount: 1, manifestPath: '/tmp/manifest2.json', createdAt: new Date().toISOString() })
    expect(useStore.getState().reviewBatches[0].id).toBe('rb-2')
  })

  it('removeReviewBatch deletes by id', () => {
    useStore.getState().addReviewBatch({ id: 'rb-1', sourceId: 'src-1', sourceLabel: 'Downloads', fileCount: 3, manifestPath: '/tmp/manifest.json', createdAt: new Date().toISOString() })
    useStore.getState().removeReviewBatch('rb-1')
    expect(useStore.getState().reviewBatches).toHaveLength(0)
  })
})
