import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMemo } from 'react'
import { CommandPalette } from '@/components/CommandPalette'
import { FirstRunOnboarding } from '@/components/FirstRunOnboarding'
import { NavRail } from '@/components/NavRail'
import { ProgressBar } from '@/components/ProgressBar'
import { TauriProvider } from '@/components/TauriProvider'
import { TitleBar } from '@/components/TitleBar'
import { Cleanup } from '@/views/Cleanup'
import { Duplicates } from '@/views/Duplicates'
import { Overview } from '@/views/Overview'
import { Settings } from '@/views/Settings'
import { Sources } from '@/views/Sources'
import { StorageMap } from '@/views/StorageMap'
import { useStore } from './store'

const views = {
  overview: Overview,
  sources: Sources,
  duplicates: Duplicates,
  map: StorageMap,
  cleanup: Cleanup,
  settings: Settings,
}

export default function App() {
  const queryClient = useMemo(() => new QueryClient(), [])

  return (
    <QueryClientProvider client={queryClient}>
      <TauriProvider>
        <AppShell />
      </TauriProvider>
    </QueryClientProvider>
  )
}

function AppShell() {
  const activeView = useStore((state) => state.activeView)
  const View = views[activeView]

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface text-text-primary">
      <TitleBar />
      <NavRail />
      <main className="ml-16 mt-9 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-[1200px] px-6 py-6">
          <View />
        </div>
      </main>
      <ProgressBar />
      <CommandPalette />
      <FirstRunOnboarding />
    </div>
  )
}
