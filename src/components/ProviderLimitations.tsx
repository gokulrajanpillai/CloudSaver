import { AlertTriangle } from 'lucide-react'
import { PROVIDER_LIMITATIONS } from '@/lib/provider-limitations'

export function ProviderLimitations() {
  return (
    <section className="rounded-lg border border-warning/30 bg-warning/10 p-4" aria-label="Provider limitations">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-warning" />
        <div className="min-w-0">
          <h2 className="text-sm font-semibold">Cloud provider limitations</h2>
          <p className="mt-1 text-xs text-text-secondary">
            CloudSaver can scan local synced folders today. Direct cloud APIs are being hardened provider by provider.
          </p>
          <dl className="mt-3 grid gap-2 md:grid-cols-2">
            {PROVIDER_LIMITATIONS.map((item) => (
              <div key={item.provider}>
                <dt className="text-xs font-semibold">{item.provider}</dt>
                <dd className="mt-0.5 text-xs leading-5 text-text-secondary">{item.limitation}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  )
}
