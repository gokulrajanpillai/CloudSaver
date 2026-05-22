import {
  BarChart3,
  Copy,
  HardDrive,
  LayoutDashboard,
  Settings,
  Trash2,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { ActiveView, useStore } from '@/store'

const items: Array<{ view: ActiveView; label: string; icon: typeof LayoutDashboard }> = [
  { view: 'overview', label: 'Overview', icon: LayoutDashboard },
  { view: 'sources', label: 'Sources', icon: HardDrive },
  { view: 'duplicates', label: 'Dupes', icon: Copy },
  { view: 'map', label: 'Map', icon: BarChart3 },
  { view: 'cleanup', label: 'Cleanup', icon: Trash2 },
]

export function NavRail() {
  const activeView = useStore((state) => state.activeView)
  const setView = useStore((state) => state.setView)
  const duplicateCount = useStore((state) => state.crossSourceGroups.length + state.duplicateGroups.length)
  const reviewBatchCount = useStore((state) => state.reviewBatches.length)

  return (
    <aside className="fixed left-0 top-7 z-40 flex h-[calc(100vh-28px)] w-16 flex-col bg-sidebar py-3 text-sidebar-text">
      <nav className="flex flex-1 flex-col items-center gap-1">
        {items.map((item) => (
          <NavButton
            key={item.view}
            active={activeView === item.view}
            badge={item.view === 'duplicates' ? duplicateCount : item.view === 'cleanup' ? reviewBatchCount : 0}
            icon={item.icon}
            label={item.label}
            onClick={() => setView(item.view)}
          />
        ))}
      </nav>
      <NavButton
        active={activeView === 'settings'}
        icon={Settings}
        label="Settings"
        onClick={() => setView('settings')}
      />
    </aside>
  )
}

function NavButton({
  active,
  badge,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean
  badge?: number
  icon: typeof LayoutDashboard
  label: string
  onClick: () => void
}) {
  return (
    <button
      className={cn(
        'relative flex h-14 w-14 flex-col items-center justify-center gap-1 rounded-md text-xs text-sidebar-muted transition-colors hover:bg-white/10 hover:text-sidebar-text',
        active && 'bg-white/12 text-sidebar-text',
      )}
      onClick={onClick}
      type="button"
    >
      <Icon className="h-5 w-5" />
      <span>{label}</span>
      {!!badge && <Badge className="absolute right-0 top-0 border-transparent bg-accent px-1 text-[10px] text-white">{badge}</Badge>}
    </button>
  )
}
