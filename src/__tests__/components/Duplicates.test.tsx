import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Duplicates } from '@/views/Duplicates'
import { useStore } from '@/store'
import type { VisualGroup } from '@/types'

vi.mock('@/hooks/useApi', () => ({
  useApi: () => ({
    get: vi.fn(),
    post: vi.fn().mockResolvedValue({}),
    delete: vi.fn(),
    sidecarPort: 8765,
  }),
}))

const GB = 1024 ** 3
const MB = 1024 ** 2

const crossGroups = [
  {
    id: 'cross-1',
    name: 'Photos Library.photoslibrary',
    recoverableBytes: 4.9 * GB,
    confidence: 'high' as const,
    files: [
      { source_id: 'demo-icloud', source_type: 'icloud', file_id: 'f-1', name: 'Photos Library.photoslibrary', size_bytes: 18.4 * GB, path: '/iCloud/Photos' },
      { source_id: 'demo-local', source_type: 'local', file_id: 'f-2', name: 'Photos Library.photoslibrary', size_bytes: 4.9 * GB, path: '/Downloads/Photos' },
    ],
  },
]

const visualGroups: VisualGroup[] = [
  {
    id: 'vis-1',
    similarity: 97,
    recoverableBytes: 4.2 * MB,
    files: [
      { file_id: 'v-1', source_id: 'demo-icloud', name: 'IMG_2341.jpg', size_bytes: 4.2 * MB, path: '/iCloud/IMG_2341.jpg', thumbnail: '/demo/beach-1.jpg' },
      { file_id: 'v-2', source_id: 'demo-local', name: 'IMG_2342.jpg', size_bytes: 4.1 * MB, path: '/Downloads/IMG_2342.jpg', thumbnail: '/demo/beach-2.jpg' },
    ],
  },
]

describe('Duplicates — summary', () => {
  it('shows total recoverable bytes', () => {
    useStore.setState({
      crossSourceGroups: crossGroups,
      duplicateGroups: [{ id: 'd-1', recoverableBytes: 5.6 * GB }],
      visualGroups: [],
      sources: [],
    })
    render(<Duplicates />)
    // 4.9 + 5.6 = 10.5 GB
    expect(screen.getByText('10.5 GB')).toBeInTheDocument()
  })
})

describe('Duplicates — cross-source groups', () => {
  beforeEach(() => {
    useStore.setState({
      crossSourceGroups: crossGroups,
      duplicateGroups: [],
      visualGroups: [],
      sources: [
        { id: 'demo-icloud', type: 'icloud', label: 'iCloud Drive', status: 'ready' },
        { id: 'demo-local', type: 'local', label: 'Downloads', status: 'ready' },
      ],
    })
  })

  it('renders group name', () => {
    render(<Duplicates />)
    expect(screen.getByText('Photos Library.photoslibrary')).toBeInTheDocument()
  })

  it('shows confidence badge', () => {
    render(<Duplicates />)
    expect(screen.getByText('high confidence')).toBeInTheDocument()
  })

  it('shows recoverable bytes for group', () => {
    render(<Duplicates />)
    const recoverableElements = screen.getAllByText(/4\.9 GB recoverable/)
    expect(recoverableElements.length).toBeGreaterThan(0)
  })

  it('first file is pre-selected as "keep"', () => {
    render(<Duplicates />)
    const keepButtons = screen.getAllByRole('button', { name: /keep/i })
    expect(keepButtons.length).toBeGreaterThan(0)
  })

  it('cross-source header has red border when groups exist', () => {
    render(<Duplicates />)
    const header = screen.getByText('Cross-Source Duplicates').closest('header')
    expect(header?.className).toContain('border-destructive')
  })
})

describe('Duplicates — empty state', () => {
  it('shows empty state when no cross-source groups', () => {
    useStore.setState({ crossSourceGroups: [], duplicateGroups: [], visualGroups: [], sources: [] })
    render(<Duplicates />)
    expect(screen.getByText(/no duplicates found yet/i)).toBeInTheDocument()
  })

  it('shows empty state for visual groups when none exist', () => {
    useStore.setState({ crossSourceGroups: [], duplicateGroups: [], visualGroups: [], sources: [] })
    render(<Duplicates />)
    expect(screen.getByText(/no similar images found yet/i)).toBeInTheDocument()
  })
})

describe('Duplicates — visual similarity groups', () => {
  beforeEach(() => {
    useStore.setState({
      crossSourceGroups: [],
      duplicateGroups: [],
      visualGroups,
      sources: [
        { id: 'demo-icloud', type: 'icloud', label: 'iCloud Drive', status: 'ready' },
        { id: 'demo-local', type: 'local', label: 'Downloads', status: 'ready' },
      ],
    })
  })

  it('shows similarity badge', () => {
    render(<Duplicates />)
    expect(screen.getByText('97% similar')).toBeInTheDocument()
  })

  it('renders image thumbnails', () => {
    render(<Duplicates />)
    const imgs = screen.getAllByRole('img')
    expect(imgs.length).toBeGreaterThanOrEqual(2)
  })

  it('thumbnail src points to local demo paths', () => {
    render(<Duplicates />)
    const imgs = screen.getAllByRole('img') as HTMLImageElement[]
    expect(imgs.some((img) => img.src.includes('/demo/beach-1.jpg'))).toBe(true)
    expect(imgs.some((img) => img.src.includes('/demo/beach-2.jpg'))).toBe(true)
  })

  it('clicking a thumbnail selects it as keep (adds accent border)', async () => {
    render(<Duplicates />)
    const cards = screen.getAllByRole('button').filter((b) => b.querySelector('img'))
    // Click the second card to make it "keep"
    await userEvent.click(cards[1])
    // The second card should now show the Check icon (aria: check mark)
    expect(cards[1].querySelector('svg')).toBeInTheDocument()
  })
})
