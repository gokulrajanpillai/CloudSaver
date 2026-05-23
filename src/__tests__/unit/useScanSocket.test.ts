import { renderHook } from '@testing-library/react'
import { act } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useScanSocket } from '@/hooks/useScanSocket'
import { useStore } from '@/store'

// ---------------------------------------------------------------------------
// Mock WebSocket
// ---------------------------------------------------------------------------
class MockWebSocket {
  static instances: MockWebSocket[] = []
  url: string
  readyState = WebSocket.OPEN
  onmessage: ((event: MessageEvent) => void) | null = null
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onerror: ((err: Event) => void) | null = null
  closedCount = 0

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  close() {
    this.readyState = WebSocket.CLOSED
    this.closedCount++
  }

  send(_data: string) {}

  // Helper: simulate a server-pushed message
  emit(data: object) {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent)
  }
}

vi.stubGlobal('WebSocket', MockWebSocket)

beforeEach(() => {
  MockWebSocket.instances = []
  useStore.setState({
    sidecarPort: 8765,
    sidecarReady: true,
    scanJobs: {},
    sources: [],
    scanResults: {},
  })
})

describe('useScanSocket — connection', () => {
  it('opens a WebSocket to the correct URL', () => {
    renderHook(() => useScanSocket('job-abc'))
    expect(MockWebSocket.instances).toHaveLength(1)
    expect(MockWebSocket.instances[0].url).toBe('ws://127.0.0.1:8765/scan/job-abc/ws')
  })

  it('does not open when sidecarPort is null', () => {
    useStore.setState({ sidecarPort: null })
    renderHook(() => useScanSocket('job-abc'))
    expect(MockWebSocket.instances).toHaveLength(0)
  })

  it('does not open when jobId is null', () => {
    renderHook(() => useScanSocket(null))
    expect(MockWebSocket.instances).toHaveLength(0)
  })

  it('closes the socket on unmount', () => {
    const { unmount } = renderHook(() => useScanSocket('job-1'))
    const ws = MockWebSocket.instances[0]
    unmount()
    expect(ws.closedCount).toBe(1)
  })
})

describe('useScanSocket — message handling', () => {
  it('updates scanJob on scanning status message', () => {
    useStore.getState().updateScanJob('job-1', {
      id: 'job-1', sourceId: 'src-1', status: 'queued', stage: 'Waiting', filesScanned: 0, currentPath: '',
    })
    renderHook(() => useScanSocket('job-1'))
    const ws = MockWebSocket.instances[0]

    act(() => {
      ws.emit({
        id: 'job-1',
        status: 'scanning',
        source_id: 'src-1',
        stage: 'Hashing',
        files_scanned: 120,
        current_path: '/Users/me/docs',
        progress: 0.4,
      })
    })

    const job = useStore.getState().scanJobs['job-1']
    expect(job.status).toBe('scanning')
    expect(job.filesScanned).toBe(120)
    expect(job.stage).toBe('Hashing')
  })

  it('calls setScanResult and updateSource on complete', () => {
    useStore.getState().addSource({ id: 'src-1', type: 'local', label: 'Downloads', status: 'scanning' })
    useStore.getState().updateScanJob('job-1', {
      id: 'job-1', sourceId: 'src-1', status: 'scanning', stage: 'Hashing', filesScanned: 0, currentPath: '',
    })

    renderHook(() => useScanSocket('job-1'))
    const ws = MockWebSocket.instances[0]

    const result = { files: [{ name: 'a.jpg', size_bytes: 1000, category: 'image', source_id: 'src-1' }], quota: { used: 1000, total: 50000 }, audit: {} }

    act(() => {
      ws.emit({ id: 'job-1', status: 'complete', source_id: 'src-1', result })
    })

    expect(useStore.getState().scanResults['src-1']).toBeDefined()
    const src = useStore.getState().sources.find((s) => s.id === 'src-1')
    expect(src?.status).toBe('ready')
    expect(src?.fileCount).toBe(1)
  })

  it('marks source as error on failed status', () => {
    useStore.getState().addSource({ id: 'src-1', type: 'local', label: 'Downloads', status: 'scanning' })
    useStore.getState().updateScanJob('job-1', {
      id: 'job-1', sourceId: 'src-1', status: 'scanning', stage: 'Hashing', filesScanned: 0, currentPath: '',
    })

    renderHook(() => useScanSocket('job-1'))
    act(() => {
      MockWebSocket.instances[0].emit({ id: 'job-1', status: 'failed', source_id: 'src-1', error: 'Permission denied' })
    })

    const src = useStore.getState().sources.find((s) => s.id === 'src-1')
    expect(src?.status).toBe('error')
    expect(src?.errorMessage).toBe('Permission denied')
  })

  it('uses existing job sourceId when message omits it', () => {
    useStore.getState().addSource({ id: 'src-1', type: 'local', label: 'Downloads', status: 'scanning' })
    useStore.getState().updateScanJob('job-1', {
      id: 'job-1', sourceId: 'src-1', status: 'scanning', stage: 'Hashing', filesScanned: 0, currentPath: '',
    })

    renderHook(() => useScanSocket('job-1'))
    act(() => {
      MockWebSocket.instances[0].emit({ id: 'job-1', status: 'scanning', files_scanned: 50 })
    })

    expect(useStore.getState().scanJobs['job-1'].filesScanned).toBe(50)
  })
})
