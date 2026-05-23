import { render, screen } from '@testing-library/react'
import { act } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { ProgressBar } from '@/components/ProgressBar'
import { useStore } from '@/store'

describe('ProgressBar — visibility', () => {
  it('renders nothing when no active scan jobs', () => {
    const { container } = render(<ProgressBar />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders when job is scanning', () => {
    useStore.getState().updateScanJob('job-1', {
      id: 'job-1', sourceId: 'src-1', sourceName: 'Downloads',
      status: 'scanning', stage: 'Hashing', filesScanned: 42, currentPath: '/tmp', progress: 0.5,
    })
    render(<ProgressBar />)
    expect(screen.getByText('Downloads')).toBeInTheDocument()
    expect(screen.getByText('42 files')).toBeInTheDocument()
    expect(screen.getByText('Hashing')).toBeInTheDocument()
  })

  it('renders when job is queued', () => {
    useStore.getState().updateScanJob('job-1', {
      id: 'job-1', sourceId: 'src-1', sourceName: 'iCloud Drive',
      status: 'queued', stage: 'Waiting', filesScanned: 0, currentPath: '', progress: 0,
    })
    render(<ProgressBar />)
    expect(screen.getByText('iCloud Drive')).toBeInTheDocument()
  })

  it('does not render for complete jobs', () => {
    useStore.getState().updateScanJob('job-1', {
      id: 'job-1', sourceId: 'src-1', sourceName: 'Downloads',
      status: 'complete', stage: 'Done', filesScanned: 100, currentPath: '', progress: 1,
    })
    const { container } = render(<ProgressBar />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders multiple active jobs', () => {
    useStore.getState().updateScanJob('job-1', {
      id: 'job-1', sourceId: 'src-1', sourceName: 'Downloads', status: 'scanning', stage: 'Hashing', filesScanned: 0, currentPath: '', progress: 0.3,
    })
    useStore.getState().updateScanJob('job-2', {
      id: 'job-2', sourceId: 'src-2', sourceName: 'iCloud Drive', status: 'queued', stage: 'Waiting', filesScanned: 0, currentPath: '', progress: 0,
    })
    render(<ProgressBar />)
    expect(screen.getByText('Downloads')).toBeInTheDocument()
    expect(screen.getByText('iCloud Drive')).toBeInTheDocument()
  })
})

describe('ProgressBar — infinite re-render regression guard', () => {
  it('does not cause excessive re-renders when job state updates rapidly', () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    useStore.getState().updateScanJob('job-1', {
      id: 'job-1', sourceId: 'src-1', status: 'scanning', stage: 'Hashing', filesScanned: 0, currentPath: '', progress: 0,
    })

    render(<ProgressBar />)

    // Fire many rapid state updates — without useShallow this would cause "Maximum update depth exceeded"
    act(() => {
      for (let i = 0; i < 20; i++) {
        useStore.getState().updateScanJob('job-1', { filesScanned: i, progress: i / 100 })
      }
    })

    // Verify React did not throw the infinite update error
    const hasInfiniteRenderError = errorSpy.mock.calls.some(
      (args) => String(args[0]).includes('Maximum update depth')
    )
    expect(hasInfiniteRenderError).toBe(false)

    errorSpy.mockRestore()
  })
})
