import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { Settings } from '@/views/Settings'
import { useStore } from '@/store'
import {
  DEMO_CROSS_SOURCE_GROUPS,
  DEMO_DUPLICATE_GROUPS,
  DEMO_SOURCES,
  DEMO_VISUAL_GROUPS,
} from '@/lib/demo'

describe('Settings — demo mode', () => {
  it('"Load demo data" button is enabled when demo is not active', () => {
    render(<Settings />)
    expect(screen.getByRole('button', { name: /load demo data/i })).toBeEnabled()
  })

  it('"Load demo data" button is disabled when demo is active', () => {
    DEMO_SOURCES.forEach((s) => useStore.getState().addSource(s))
    render(<Settings />)
    expect(screen.getByRole('button', { name: /load demo data/i })).toBeDisabled()
  })

  it('loading demo data populates sources', async () => {
    render(<Settings />)
    await userEvent.click(screen.getByRole('button', { name: /load demo data/i }))
    const sources = useStore.getState().sources
    expect(sources.length).toBeGreaterThanOrEqual(DEMO_SOURCES.length)
    expect(sources.some((s) => s.id === 'demo-icloud')).toBe(true)
  })

  it('loading demo data populates crossSourceGroups', async () => {
    render(<Settings />)
    await userEvent.click(screen.getByRole('button', { name: /load demo data/i }))
    expect(useStore.getState().crossSourceGroups).toHaveLength(DEMO_CROSS_SOURCE_GROUPS.length)
  })

  it('loading demo data populates visualGroups', async () => {
    render(<Settings />)
    await userEvent.click(screen.getByRole('button', { name: /load demo data/i }))
    expect(useStore.getState().visualGroups).toHaveLength(DEMO_VISUAL_GROUPS.length)
  })

  it('loading demo data populates duplicateGroups', async () => {
    render(<Settings />)
    await userEvent.click(screen.getByRole('button', { name: /load demo data/i }))
    expect(useStore.getState().duplicateGroups).toHaveLength(DEMO_DUPLICATE_GROUPS.length)
  })

  it('"Clear demo data" removes demo sources and clears groups', async () => {
    render(<Settings />)
    await userEvent.click(screen.getByRole('button', { name: /load demo data/i }))
    await userEvent.click(screen.getByRole('button', { name: /clear demo data/i }))
    expect(useStore.getState().sources.filter((s) => s.id.startsWith('demo-'))).toHaveLength(0)
    expect(useStore.getState().crossSourceGroups).toHaveLength(0)
    expect(useStore.getState().visualGroups).toHaveLength(0)
  })

  it('shows "Demo data is active" notice when demo is active', async () => {
    render(<Settings />)
    await userEvent.click(screen.getByRole('button', { name: /load demo data/i }))
    expect(screen.getByText(/demo data is active/i)).toBeInTheDocument()
  })
})

describe('Settings — theme selector', () => {
  it('changes theme when select changes', async () => {
    render(<Settings />)
    const select = screen.getByRole('combobox')
    await userEvent.selectOptions(select, 'dark')
    expect(useStore.getState().theme).toBe('dark')
  })
})

describe('Settings — toggle', () => {
  it('renders toggle switches with role="switch"', () => {
    render(<Settings />)
    const toggles = screen.getAllByRole('switch')
    expect(toggles.length).toBeGreaterThanOrEqual(2)
  })

  it('Privacy toggle (first) defaults to aria-checked=false', () => {
    render(<Settings />)
    const [privacyToggle] = screen.getAllByRole('switch')
    expect(privacyToggle).toHaveAttribute('aria-checked', 'false')
  })

  it('Privacy toggle changes aria-checked on click', async () => {
    render(<Settings />)
    const [privacyToggle] = screen.getAllByRole('switch')
    await userEvent.click(privacyToggle)
    expect(privacyToggle).toHaveAttribute('aria-checked', 'true')
  })

  it('Auto-update toggle (second) defaults to aria-checked=true', () => {
    render(<Settings />)
    const [, autoUpdateToggle] = screen.getAllByRole('switch')
    expect(autoUpdateToggle).toHaveAttribute('aria-checked', 'true')
  })
})

describe('Settings — connected accounts', () => {
  it('shows "Disconnect" for connected Google Drive account', () => {
    useStore.getState().addSource({
      id: 'gdrive-1', type: 'google_drive', label: 'Drive', driveAccountEmail: 'user@gmail.com', status: 'ready',
    })
    render(<Settings />)
    expect(screen.getByText('user@gmail.com')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /disconnect/i })).toBeInTheDocument()
  })

  it('clicking Disconnect removes the source', async () => {
    useStore.getState().addSource({
      id: 'gdrive-1', type: 'google_drive', label: 'Drive', driveAccountEmail: 'user@gmail.com', status: 'ready',
    })
    render(<Settings />)
    await userEvent.click(screen.getByRole('button', { name: /disconnect/i }))
    expect(useStore.getState().sources.find((s) => s.id === 'gdrive-1')).toBeUndefined()
  })
})
