import { Command } from 'cmdk'
import { useEffect } from 'react'
import { useStore, type ActiveView } from '@/store'

const views: ActiveView[] = ['overview', 'sources', 'duplicates', 'map', 'cleanup', 'settings']

const labels: Record<ActiveView, string> = {
  overview: 'Overview',
  sources: 'Sources',
  duplicates: 'Duplicates',
  map: 'Storage Map',
  cleanup: 'Cleanup',
  settings: 'Settings',
}

export function CommandPalette() {
  const open = useStore((state) => state.commandPaletteOpen)
  const setOpen = useStore((state) => state.setCommandPaletteOpen)
  const setView = useStore((state) => state.setView)

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setOpen(!open)
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, setOpen])

  return (
    <Command.Dialog
      className="fixed left-1/2 top-24 z-[80] w-[min(560px,calc(100vw-32px))] -translate-x-1/2 overflow-hidden rounded-lg border border-border bg-surface shadow-2xl"
      label="Global command palette"
      onOpenChange={setOpen}
      open={open}
      overlayClassName="fixed inset-0 z-[70] bg-black/25 backdrop-blur-sm"
    >
      <Command.Input
        className="h-12 w-full border-b border-border bg-transparent px-4 text-sm outline-none placeholder:text-text-muted"
        placeholder="Search actions, sources, views..."
      />
      <Command.List className="max-h-[360px] overflow-y-auto p-2">
        <Command.Empty className="px-3 py-6 text-center text-sm text-text-muted">
          No matching commands
        </Command.Empty>
        <Command.Group className="p-1" heading="Navigate">
          {views.map((view) => (
            <Command.Item
              className="cursor-pointer rounded-md px-3 py-2 text-sm text-text-primary aria-selected:bg-surface-overlay"
              key={view}
              onSelect={() => {
                setView(view)
                setOpen(false)
              }}
            >
              {labels[view]}
            </Command.Item>
          ))}
        </Command.Group>
        <Command.Group className="p-1" heading="Actions">
          <Command.Item className="cursor-pointer rounded-md px-3 py-2 text-sm aria-selected:bg-surface-overlay">
            Add Source
          </Command.Item>
          <Command.Item className="cursor-pointer rounded-md px-3 py-2 text-sm aria-selected:bg-surface-overlay">
            Scan All Sources
          </Command.Item>
          <Command.Item className="cursor-pointer rounded-md px-3 py-2 text-sm aria-selected:bg-surface-overlay">
            Export Report
          </Command.Item>
        </Command.Group>
      </Command.List>
    </Command.Dialog>
  )
}
