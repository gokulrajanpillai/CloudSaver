import { useEffect, useState } from 'react'
import { MaturityBadge } from '@/components/MaturityBadge'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { useApi } from '@/hooks/useApi'
import {
  DEMO_CROSS_SOURCE_GROUPS,
  DEMO_DUPLICATE_GROUPS,
  DEMO_SCAN_RESULTS,
  DEMO_SOURCES,
  DEMO_VISUAL_GROUPS,
} from '@/lib/demo'
import { useStore } from '@/store'

export function Settings() {
  const api = useApi()
  const sources = useStore((state) => state.sources)
  const sidecarReady = useStore((state) => state.sidecarReady)
  const theme = useStore((state) => state.theme)
  const setTheme = useStore((state) => state.setTheme)
  const removeSource = useStore((state) => state.removeSource)
  const addSource = useStore((state) => state.addSource)
  const setScanResult = useStore((state) => state.setScanResult)
  const setCrossSourceGroups = useStore((state) => state.setCrossSourceGroups)
  const setDuplicateGroups = useStore((state) => state.setDuplicateGroups)
  const setVisualGroups = useStore((state) => state.setVisualGroups)
  const driveAccounts = sources.filter((source) => source.type === 'google_drive')
  const icloud = sources.find((source) => source.type === 'icloud')
  const [disableDiagnostics, setDisableDiagnostics] = useState(false)
  const [autoUpdate, setAutoUpdate] = useState(true)
  const [exportingDiagnostics, setExportingDiagnostics] = useState(false)

  const isDemoActive = sources.some((s) => s.id.startsWith('demo-'))

  useEffect(() => {
    if (!sidecarReady) return
    api
      .get<{ local_diagnostics_enabled: boolean }>('/privacy/settings')
      .then((settings) => setDisableDiagnostics(!settings.local_diagnostics_enabled))
      .catch(() => undefined)
  }, [api, sidecarReady])

  async function updateDiagnosticsDisabled(disabled: boolean) {
    setDisableDiagnostics(disabled)
    if (!sidecarReady) return
    try {
      const settings = await api.post<{ local_diagnostics_enabled: boolean }>('/privacy/settings', {
        local_diagnostics_enabled: !disabled,
      })
      setDisableDiagnostics(!settings.local_diagnostics_enabled)
    } catch {
      setDisableDiagnostics(!disabled)
    }
  }

  async function exportDiagnostics() {
    if (!sidecarReady) return
    setExportingDiagnostics(true)
    try {
      const bundle = await api.get<Record<string, unknown>>('/diagnostics/export')
      const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `cloudsaver-diagnostics-${new Date().toISOString().slice(0, 10)}.json`
      link.click()
      URL.revokeObjectURL(url)
    } finally {
      setExportingDiagnostics(false)
    }
  }

  function loadDemo() {
    DEMO_SOURCES.forEach((s) => addSource(s))
    Object.entries(DEMO_SCAN_RESULTS).forEach(([id, result]) => setScanResult(id, result))
    setCrossSourceGroups(DEMO_CROSS_SOURCE_GROUPS)
    setDuplicateGroups(DEMO_DUPLICATE_GROUPS)
    setVisualGroups(DEMO_VISUAL_GROUPS)
  }

  function clearDemo() {
    DEMO_SOURCES.forEach((s) => removeSource(s.id))
    setCrossSourceGroups([])
    setDuplicateGroups([])
    setVisualGroups([])
  }

  return (
    <section className="space-y-4">
      <h1 className="text-lg font-semibold">Settings</h1>
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
      <SettingsSection maturity="preview" title="License">
        <div className="flex gap-2">
          <input className="h-9 flex-1 rounded-md border border-border bg-surface px-3 text-sm" placeholder="License key" />
          <Button type="button">Activate</Button>
        </div>
      </SettingsSection>
      <SettingsSection maturity="production" title="Appearance">
        <Select value={theme} onChange={(event) => setTheme(event.target.value as typeof theme)}>
          <option value="system">System</option>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </Select>
      </SettingsSection>
      <SettingsSection maturity="preview" title="Privacy">
        <Toggle checked={disableDiagnostics} label="Disable local diagnostics" onChange={(value) => void updateDiagnosticsDisabled(value)} />
        <div className="mt-3 flex items-center justify-between gap-3 rounded-md border border-border p-3">
          <div>
            <p className="text-sm font-medium">Redacted diagnostics export</p>
            <p className="mt-1 text-xs text-text-muted">Includes runtime and feature state. File names, paths, emails, and scan results are excluded or redacted.</p>
          </div>
          <Button disabled={!sidecarReady || exportingDiagnostics} onClick={() => void exportDiagnostics()} size="sm" type="button" variant="outline">
            {exportingDiagnostics ? 'Exporting...' : 'Export'}
          </Button>
        </div>
        <a className="mt-3 block text-sm text-accent hover:text-accent-hover" href="https://github.com/gokulrajanpillai/CloudSaver/blob/main/PRIVACY.md">
          Privacy policy
        </a>
      </SettingsSection>
      <SettingsSection maturity="preview" title="AI Advisor">
        <p className="text-sm text-text-muted">Enter an API key to enable AI-powered storage recommendations.</p>
        <input className="mt-2 h-9 w-full rounded-md border border-border bg-surface px-3 text-sm" placeholder="API key" />
      </SettingsSection>
      <SettingsSection maturity="preview" title="Updates">
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-muted">Version 1.1.0</span>
          <Button size="sm" type="button" variant="outline">Check for updates</Button>
        </div>
        <div className="mt-3">
          <Toggle checked={autoUpdate} label="Auto-update" onChange={setAutoUpdate} />
        </div>
      </SettingsSection>
      <SettingsSection maturity="production" title="Demo Mode">
        <p className="text-sm text-text-muted">Load sample data to explore the app without scanning real files.</p>
        <div className="mt-3 flex gap-2">
          <Button disabled={isDemoActive} onClick={loadDemo} size="sm" type="button">
            Load demo data
          </Button>
          <Button disabled={!isDemoActive} onClick={clearDemo} size="sm" type="button" variant="outline">
            Clear demo data
          </Button>
        </div>
        {isDemoActive && <p className="mt-2 text-xs text-accent">Demo data is active — figures shown are illustrative.</p>}
      </SettingsSection>
      <SettingsSection maturity="production" title="About">
        <div className="space-x-4 text-sm">
          <a className="text-accent" href="https://github.com/gokulrajanpillai/CloudSaver">GitHub</a>
          <a className="text-accent" href="https://github.com/gokulrajanpillai/CloudSaver/blob/main/CHANGELOG.md">Changelog</a>
        </div>
      </SettingsSection>
    </section>
  )
}

function Toggle({ checked, label, onChange }: { checked: boolean; label: string; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm">{label}</span>
      <button
        aria-checked={checked}
        className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 ${checked ? 'bg-accent' : 'bg-border'}`}
        onClick={() => onChange(!checked)}
        role="switch"
        type="button"
      >
        <span
          className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ${checked ? 'translate-x-4' : 'translate-x-0'}`}
        />
      </button>
    </div>
  )
}

function SettingsSection({
  children,
  maturity,
  title,
}: {
  children: React.ReactNode
  maturity?: React.ComponentProps<typeof MaturityBadge>['maturity']
  title: string
}) {
  return (
    <section className="rounded-lg border border-border bg-surface-raised p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold">{title}</h2>
        {maturity && <MaturityBadge maturity={maturity} />}
      </div>
      {children}
    </section>
  )
}
