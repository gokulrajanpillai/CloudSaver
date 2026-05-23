import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { NavRail } from '@/components/NavRail'
import { useStore } from '@/store'

describe('NavRail', () => {
  it('renders all 5 main navigation items plus Settings', () => {
    render(<NavRail />)
    expect(screen.getByRole('button', { name: /overview/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sources/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /dupes/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /map/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cleanup/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument()
  })

  it('clicking a nav item calls setView', async () => {
    render(<NavRail />)
    await userEvent.click(screen.getByRole('button', { name: /sources/i }))
    expect(useStore.getState().activeView).toBe('sources')
  })

  it('clicking Settings calls setView("settings")', async () => {
    render(<NavRail />)
    await userEvent.click(screen.getByRole('button', { name: /settings/i }))
    expect(useStore.getState().activeView).toBe('settings')
  })

  it('shows duplicate count badge when cross-source groups exist', () => {
    useStore.setState({ crossSourceGroups: [{ id: 'g-1' }, { id: 'g-2' }] })
    render(<NavRail />)
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('shows no duplicate badge when count is zero', () => {
    useStore.setState({ crossSourceGroups: [], duplicateGroups: [] })
    render(<NavRail />)
    expect(screen.queryByText('0')).not.toBeInTheDocument()
  })
})
