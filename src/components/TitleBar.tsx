import { Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store'

export function TitleBar() {
  const setCommandPaletteOpen = useStore((state) => state.setCommandPaletteOpen)

  return (
    <header
      className="fixed left-0 right-0 top-0 z-50 flex h-9 items-center justify-center border-b border-border bg-surface/95 text-xs text-text-secondary backdrop-blur"
      data-tauri-drag-region
    >
      <span className="font-medium" data-tauri-drag-region>
        CloudSaver
      </span>
      <div className="absolute right-2 top-1/2 -translate-y-1/2">
        <Button
          aria-label="Open command palette"
          className="h-6 gap-1 px-2 text-xs"
          onClick={() => setCommandPaletteOpen(true)}
          size="sm"
          type="button"
          variant="ghost"
        >
          <Search className="h-3.5 w-3.5" />
          <span>⌘K</span>
        </Button>
      </div>
    </header>
  )
}
