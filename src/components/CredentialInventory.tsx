import { KeyRound, Trash2 } from 'lucide-react'
import { MaturityBadge } from '@/components/MaturityBadge'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useStore } from '@/store'

export function CredentialInventory() {
  const sources = useStore((state) => state.sources)
  const removeSource = useStore((state) => state.removeSource)
  const accounts = sources.filter((source) => source.type === 'google_drive')

  return (
    <section className="rounded-lg border border-border bg-surface-raised p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-accent/10">
            <KeyRound className="h-5 w-5 text-accent" />
          </div>
          <div>
            <h2 className="text-sm font-semibold">Credential inventory</h2>
            <p className="mt-1 text-xs text-text-secondary">
              Connected account records are shown without access tokens, refresh tokens, or raw secrets.
            </p>
          </div>
        </div>
        <MaturityBadge maturity="preview" />
      </div>

      <div className="mt-4 space-y-2">
        {accounts.map((source) => (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border bg-surface p-3" key={source.id}>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-medium">{source.label}</span>
                <Badge>{source.type.replace('_', ' ')}</Badge>
                <Badge>{source.accessToken ? 'Access token in memory' : 'No in-memory token'}</Badge>
              </div>
              <p className="mt-1 truncate text-xs text-text-muted">
                Account: {source.driveAccountEmail || 'Unknown'} · Last scanned: {source.lastScanned || 'Never'}
              </p>
            </div>
            <Button onClick={() => removeSource(source.id)} size="sm" type="button" variant="outline">
              <Trash2 className="h-3.5 w-3.5" />
              Disconnect
            </Button>
          </div>
        ))}
        {!accounts.length && (
          <p className="rounded-md border border-dashed border-border bg-surface p-3 text-sm text-text-muted">
            No direct provider credentials are connected. Local and synced-folder scans do not require stored provider secrets.
          </p>
        )}
      </div>
    </section>
  )
}
