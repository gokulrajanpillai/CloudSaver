import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { Overview } from '@/views/Overview'
import { useStore } from '@/store'
import type { Source, ScanResult } from '@/types'

const GB = 1024 ** 3
const MB = 1024 ** 2

const icloudSource: Source = {
  id: 'src-icloud', type: 'icloud', label: 'iCloud Drive', status: 'ready',
  fileCount: 9841, totalBytes: 34.2 * GB,
}

const icloudResult: ScanResult = {
  sourceId: 'src-icloud',
  quota: { used: 34.2 * GB, total: 50 * GB },
  audit: { opportunities: { image_optimization_bytes: 2.1 * GB } },
  files: [
    { name: 'Photos Library.photoslibrary', size_bytes: 18.4 * GB, category: 'image', source_id: 'src-icloud' },
    { name: 'Documents.zip', size_bytes: 4.2 * GB, category: 'archive', source_id: 'src-icloud' },
  ],
}

describe('Overview — empty state', () => {
  it('shows onboarding hero when no sources', () => {
    render(<Overview />)
    expect(screen.getByText(/scan your first source/i)).toBeInTheDocument()
  })

  it('shows "Connect a source" CTA button', () => {
    render(<Overview />)
    expect(screen.getByRole('button', { name: /connect a source/i })).toBeInTheDocument()
  })

  it('clicking CTA navigates to sources view', async () => {
    render(<Overview />)
    await userEvent.click(screen.getByRole('button', { name: /connect a source/i }))
    expect(useStore.getState().activeView).toBe('sources')
  })
})

describe('Overview — with data', () => {
  beforeEach(() => {
    useStore.setState({
      sources: [icloudSource],
      scanResults: { 'src-icloud': icloudResult },
      crossSourceGroups: [{ id: 'g-1', recoverableBytes: 4.9 * GB }],
      duplicateGroups: [],
    })
  })

  it('shows total storage metric', () => {
    render(<Overview />)
    // Sum of file sizes: 18.4 + 4.2 = 22.6 GB
    expect(screen.getByText('22.6 GB')).toBeInTheDocument()
  })

  it('shows file count metric', () => {
    render(<Overview />)
    expect(screen.getByText('2')).toBeInTheDocument() // 2 files in icloudResult
  })

  it('shows duplicates count', () => {
    render(<Overview />)
    expect(screen.getByText('1')).toBeInTheDocument() // 1 crossSourceGroup
  })

  it('shows image savings metric', () => {
    render(<Overview />)
    expect(screen.getByText('2.1 GB')).toBeInTheDocument()
  })

  it('shows "Remove extra copies" plan card', () => {
    render(<Overview />)
    expect(screen.getByText(/remove extra copies/i)).toBeInTheDocument()
  })

  it('"Re-encode video" card is disabled', () => {
    render(<Overview />)
    expect(screen.getByRole('button', { name: /learn how to unlock/i })).toBeDisabled()
  })

  it('clicking "Review duplicates" navigates to duplicates view', async () => {
    render(<Overview />)
    await userEvent.click(screen.getByRole('button', { name: /review duplicates/i }))
    expect(useStore.getState().activeView).toBe('duplicates')
  })

  it('detects iCloud provider for default plan selector', () => {
    render(<Overview />)
    // iCloud+ 200 GB should be auto-selected
    const select = screen.getByRole('combobox')
    expect((select as HTMLSelectElement).value).toBe('icloud_200')
  })

  it('detects Google One provider when google_drive source present', () => {
    useStore.setState({ sources: [{ id: 'g', type: 'google_drive', label: 'Drive', status: 'ready' }] })
    render(<Overview />)
    const select = screen.getByRole('combobox')
    expect((select as HTMLSelectElement).value).toBe('google_one_100')
  })

  it('shows monthly cost as non-zero dollar amount', () => {
    render(<Overview />)
    expect(screen.getByText(/\$\d+\.\d+/)).toBeInTheDocument()
  })
})
