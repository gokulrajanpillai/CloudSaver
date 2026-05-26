import { Badge } from '@/components/ui/badge'
import { PROVIDER_CAPABILITIES, type ProviderCapabilityState } from '@/lib/provider-capabilities'
import { cn } from '@/lib/utils'

const capabilityLabels: Record<ProviderCapabilityState, string> = {
  supported: 'Supported',
  partial: 'Partial',
  planned: 'Planned',
  unsupported: 'No',
}

const capabilityClassNames: Record<ProviderCapabilityState, string> = {
  supported: 'bg-success/10 text-success border-success/30',
  partial: 'bg-warning/10 text-warning border-warning/30',
  planned: 'bg-surface-overlay text-text-secondary',
  unsupported: 'bg-surface text-text-muted',
}

export function ProviderCapabilityMatrix() {
  return (
    <section className="rounded-lg border border-border bg-surface-raised p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold">Provider capability matrix</h2>
          <p className="mt-1 text-xs text-text-secondary">
            Capability varies by provider and by direct API versus local synced-folder workflows.
          </p>
        </div>
        <Badge>Visible before use</Badge>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-left text-xs">
          <thead className="text-text-muted">
            <tr className="border-b border-border">
              <th className="py-2 pr-3 font-medium">Provider</th>
              <th className="px-3 py-2 font-medium">Maturity</th>
              <th className="px-3 py-2 font-medium">Scan</th>
              <th className="px-3 py-2 font-medium">Quota</th>
              <th className="px-3 py-2 font-medium">Duplicates</th>
              <th className="px-3 py-2 font-medium">Cleanup</th>
              <th className="px-3 py-2 font-medium">Restore</th>
              <th className="py-2 pl-3 font-medium">Notes</th>
            </tr>
          </thead>
          <tbody>
            {PROVIDER_CAPABILITIES.map((provider) => (
              <tr className="border-b border-border last:border-0" key={provider.key}>
                <td className="py-3 pr-3 font-medium">{provider.label}</td>
                <td className="px-3 py-3 capitalize text-text-secondary">{provider.maturity}</td>
                <CapabilityCell state={provider.scan} />
                <CapabilityCell state={provider.quota} />
                <CapabilityCell state={provider.duplicates} />
                <CapabilityCell state={provider.cleanup} />
                <CapabilityCell state={provider.restore} />
                <td className="py-3 pl-3 text-text-secondary">{provider.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function CapabilityCell({ state }: { state: ProviderCapabilityState }) {
  return (
    <td className="px-3 py-3">
      <span
        className={cn(
          'inline-flex min-w-20 justify-center rounded-md border px-2 py-1 font-medium',
          capabilityClassNames[state],
        )}
      >
        {capabilityLabels[state]}
      </span>
    </td>
  )
}
