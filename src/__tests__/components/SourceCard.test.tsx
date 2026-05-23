import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { SourceCard } from '@/components/SourceCard'
import type { Source } from '@/types'

const GB = 1024 ** 3

const makeSource = (overrides: Partial<Source> = {}): Source => ({
  id: 'src-1',
  type: 'local',
  label: 'Downloads',
  path: '/Users/me/Downloads',
  status: 'idle',
  fileCount: 2304,
  totalBytes: 12.8 * GB,
  ...overrides,
})

describe('SourceCard — rendering', () => {
  it('shows the source label', () => {
    render(<SourceCard source={makeSource()} />)
    expect(screen.getByText('Downloads')).toBeInTheDocument()
  })

  it('shows the path', () => {
    render(<SourceCard source={makeSource()} />)
    expect(screen.getByText('/Users/me/Downloads')).toBeInTheDocument()
  })

  it('shows driveAccountEmail when path is absent', () => {
    render(<SourceCard source={makeSource({ path: undefined, driveAccountEmail: 'user@example.com' })} />)
    expect(screen.getByText('user@example.com')).toBeInTheDocument()
  })

  it('shows "No path" when neither path nor email', () => {
    render(<SourceCard source={makeSource({ path: undefined })} />)
    expect(screen.getByText('No path')).toBeInTheDocument()
  })

  it('shows file count and size', () => {
    render(<SourceCard source={makeSource()} />)
    expect(screen.getByText(/2304 files/)).toBeInTheDocument()
  })

  it('shows quota progress bar when quota is present', () => {
    const source = makeSource({ quota: { used: 34 * GB, total: 50 * GB } })
    render(<SourceCard source={source} />)
    // progress bar container exists
    expect(screen.getByText(/34\.0 GB used/)).toBeInTheDocument()
  })

  it('does not show progress bar without quota', () => {
    render(<SourceCard source={makeSource({ quota: undefined })} />)
    expect(screen.queryByText(/used/)).not.toBeInTheDocument()
  })

  it('shows "Storage nearly full" warning when quota >90%', () => {
    const source = makeSource({ quota: { used: 48 * GB, total: 50 * GB } })
    render(<SourceCard source={source} />)
    expect(screen.getByText(/storage nearly full/i)).toBeInTheDocument()
  })

  it('does not show storage warning when quota is <90%', () => {
    const source = makeSource({ quota: { used: 30 * GB, total: 50 * GB } })
    render(<SourceCard source={source} />)
    expect(screen.queryByText(/storage nearly full/i)).not.toBeInTheDocument()
  })
})

describe('SourceCard — scan button', () => {
  it('calls onScan when "Scan now" is clicked', async () => {
    const onScan = vi.fn()
    render(<SourceCard onScan={onScan} source={makeSource()} />)
    await userEvent.click(screen.getByRole('button', { name: /scan now/i }))
    expect(onScan).toHaveBeenCalledOnce()
  })

  it('disables scan button when status is scanning', () => {
    render(<SourceCard source={makeSource({ status: 'scanning' })} />)
    expect(screen.getByRole('button', { name: /scan now/i })).toBeDisabled()
  })

  it('enables scan button when status is idle', () => {
    render(<SourceCard source={makeSource({ status: 'idle' })} />)
    expect(screen.getByRole('button', { name: /scan now/i })).toBeEnabled()
  })
})

describe('SourceCard — remove menu', () => {
  it('does not call onRemove directly from MoreHorizontal click', async () => {
    const onRemove = vi.fn()
    render(<SourceCard onRemove={onRemove} source={makeSource()} />)
    await userEvent.click(screen.getByRole('button', { name: /source menu/i }))
    // onRemove should NOT have been called yet — dropdown must appear first
    expect(onRemove).not.toHaveBeenCalled()
  })

  it('shows "Remove source" in dropdown after menu click', async () => {
    render(<SourceCard onRemove={() => {}} source={makeSource()} />)
    await userEvent.click(screen.getByRole('button', { name: /source menu/i }))
    expect(screen.getByText(/remove source/i)).toBeInTheDocument()
  })

  it('calls onRemove when "Remove source" is clicked in dropdown', async () => {
    const onRemove = vi.fn()
    render(<SourceCard onRemove={onRemove} source={makeSource()} />)
    await userEvent.click(screen.getByRole('button', { name: /source menu/i }))
    await userEvent.click(screen.getByText(/remove source/i))
    expect(onRemove).toHaveBeenCalledOnce()
  })
})
