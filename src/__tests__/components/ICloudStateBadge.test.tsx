import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ICloudStateBadge, canRevealICloudFile } from '@/components/ICloudStateBadge'

describe('ICloudStateBadge — rendering', () => {
  it('renders nothing for undefined state', () => {
    const { container } = render(<ICloudStateBadge />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing for null state', () => {
    const { container } = render(<ICloudStateBadge state={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing for "local" state', () => {
    const { container } = render(<ICloudStateBadge state="local" />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders "iCloud only" badge for evicted state', () => {
    render(<ICloudStateBadge state="evicted" />)
    expect(screen.getByText('iCloud only')).toBeInTheDocument()
  })

  it('renders "Downloading" badge for downloading state', () => {
    render(<ICloudStateBadge state="downloading" />)
    expect(screen.getByText('Downloading')).toBeInTheDocument()
  })

  it('shows "Manage in iCloud" button only for evicted state when onManage provided', () => {
    render(<ICloudStateBadge state="evicted" onManage={() => {}} />)
    expect(screen.getByRole('button', { name: /manage in icloud/i })).toBeInTheDocument()
  })

  it('does not show manage button for downloading state', () => {
    render(<ICloudStateBadge state="downloading" onManage={() => {}} />)
    expect(screen.queryByRole('button', { name: /manage/i })).not.toBeInTheDocument()
  })
})

describe('canRevealICloudFile', () => {
  it('returns false for evicted', () => expect(canRevealICloudFile('evicted')).toBe(false))
  it('returns true for local', () => expect(canRevealICloudFile('local')).toBe(true))
  it('returns true for undefined', () => expect(canRevealICloudFile(undefined)).toBe(true))
  it('returns true for null', () => expect(canRevealICloudFile(null)).toBe(true))
  it('returns true for downloading', () => expect(canRevealICloudFile('downloading')).toBe(true))
})
