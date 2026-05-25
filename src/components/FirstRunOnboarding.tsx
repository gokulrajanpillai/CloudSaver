import { Cloud, FolderOpen, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useStore } from '@/store'

const choices = [
  {
    title: 'Scan a local folder',
    description: 'Best first scan. Choose Downloads, Pictures, Desktop, an external drive, or a project folder.',
    icon: FolderOpen,
    view: 'sources' as const,
  },
  {
    title: 'Scan a synced cloud folder',
    description: 'Use iCloud Drive, Google Drive, Dropbox, or OneDrive folders already synced to this device.',
    icon: Cloud,
    view: 'sources' as const,
  },
  {
    title: 'Connect a provider account',
    description: 'Use direct provider APIs where available. Production support varies by provider.',
    icon: ShieldCheck,
    view: 'sources' as const,
  },
]

export function FirstRunOnboarding() {
  const onboardingComplete = useStore((state) => state.onboardingComplete)
  const setOnboardingComplete = useStore((state) => state.setOnboardingComplete)
  const setView = useStore((state) => state.setView)

  if (onboardingComplete) return null

  function choose(view: 'sources') {
    setView(view)
    setOnboardingComplete(true)
  }

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/40 px-4">
      <section
        aria-label="First-run onboarding"
        className="w-full max-w-3xl rounded-lg border border-border bg-surface p-5 shadow-xl"
      >
        <div className="flex items-start justify-between gap-4 border-b border-border pb-4">
          <div>
            <h1 className="text-lg font-semibold">Choose your first storage audit</h1>
            <p className="mt-1 max-w-xl text-sm text-text-secondary">
              CloudSaver starts with sources you explicitly add. Files stay on this device unless
              you opt into a provider, update, payment, AI, or team feature.
            </p>
          </div>
          <Button onClick={() => setOnboardingComplete(true)} type="button" variant="ghost">
            Later
          </Button>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {choices.map((choice) => (
            <button
              className="rounded-lg border border-border bg-surface-raised p-4 text-left transition-colors hover:border-accent hover:bg-surface-overlay"
              key={choice.title}
              onClick={() => choose(choice.view)}
              type="button"
            >
              <choice.icon className="h-5 w-5 text-accent" />
              <h2 className="mt-3 text-sm font-semibold">{choice.title}</h2>
              <p className="mt-2 text-xs leading-5 text-text-secondary">{choice.description}</p>
            </button>
          ))}
        </div>
      </section>
    </div>
  )
}
