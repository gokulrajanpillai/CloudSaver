import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { useStore } from '@/store'

export function Settings() {
  const sources = useStore((state) => state.sources)
  const theme = useStore((state) => state.theme)
  const setTheme = useStore((state) => state.setTheme)
  const removeSource = useStore((state) => state.removeSource)
  const driveAccounts = sources.filter((source) => source.type === 'google_drive')
  const icloud = sources.find((source) => source.type === 'icloud')

  return (
    <section className="space-y-4">
      <h1 className="text-[18px] font-semibold">Settings</h1>
      <SettingsSection title="Connected Accounts">
        <div className="space-y-2">
          {driveAccounts.map((source) => (
            <div className="flex items-center justify-between rounded-md border border-border p-3" key={source.id}>
              <span className="text-sm">{source.driveAccountEmail}</span>
              <Button onClick={() => removeSource(source.id)} size="sm" type="button" variant="outline">
                Disconnect
              </Button>
            </div>
          ))}
          <p className="text-sm text-text-muted">{icloud ? 'iCloud Drive connected' : 'No iCloud account detected'}</p>
        </div>
      </SettingsSection>
      <SettingsSection title="License">
        <div className="flex gap-2">
          <input className="h-9 flex-1 rounded-md border border-border bg-surface px-3 text-sm" placeholder="License key" />
          <Button type="button">Activate</Button>
        </div>
      </SettingsSection>
      <SettingsSection title="Appearance">
        <Select value={theme} onChange={(event) => setTheme(event.target.value as typeof theme)}>
          <option value="system">System</option>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </Select>
      </SettingsSection>
      <SettingsSection title="Privacy">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" /> Disable local diagnostics
        </label>
        <a className="text-sm text-accent" href="https://github.com/gokulrajanpillai/CloudSaver/blob/main/PRIVACY.md">
          Privacy policy
        </a>
      </SettingsSection>
      <SettingsSection title="AI Advisor">
        <p className="text-sm text-text-muted">Status: unavailable until configured</p>
        <input className="mt-2 h-9 w-full rounded-md border border-border bg-surface px-3 text-sm" placeholder="API key" />
      </SettingsSection>
      <SettingsSection title="Updates">
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-muted">Version 1.1.0</span>
          <Button size="sm" type="button" variant="outline">Check for updates</Button>
        </div>
        <label className="mt-3 flex items-center gap-2 text-sm">
          <input type="checkbox" /> Auto-update
        </label>
      </SettingsSection>
      <SettingsSection title="About">
        <div className="space-x-4 text-sm">
          <a className="text-accent" href="https://github.com/gokulrajanpillai/CloudSaver">GitHub</a>
          <a className="text-accent" href="https://github.com/gokulrajanpillai/CloudSaver/blob/main/CHANGELOG.md">Changelog</a>
        </div>
      </SettingsSection>
    </section>
  )
}

function SettingsSection({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <section className="rounded-lg border border-border bg-surface-raised p-4">
      <h2 className="mb-3 text-sm font-semibold">{title}</h2>
      {children}
    </section>
  )
}
