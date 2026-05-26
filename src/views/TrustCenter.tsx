import { Brain, CreditCard, RefreshCw, ShieldCheck, Users } from 'lucide-react'
import { ProductContract } from '@/components/ProductContract'
import { ProviderCapabilityMatrix } from '@/components/ProviderCapabilityMatrix'
import { Badge } from '@/components/ui/badge'

const networkPaths = [
  {
    icon: RefreshCw,
    title: 'Update checks',
    status: 'Opt-in or configured',
    data: 'Current app version and update channel.',
  },
  {
    icon: CreditCard,
    title: 'Payments',
    status: 'Only during checkout',
    data: 'Plan, checkout metadata, and customer email if entered.',
  },
  {
    icon: Brain,
    title: 'AI Advisor',
    status: 'Optional',
    data: 'Redacted counts, sizes, categories, and savings estimates. No paths or filenames.',
  },
  {
    icon: Users,
    title: 'Team workspace',
    status: 'Business preview',
    data: 'Redacted audit summaries with root paths stripped.',
  },
]

export function TrustCenter() {
  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <h1 className="text-lg font-semibold">Trust Center</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Review the privacy boundary, optional network paths, and safety model before connecting storage.
          </p>
        </div>
        <ShieldCheck className="h-6 w-6 text-accent" />
      </div>

      <ProductContract />
      <ProviderCapabilityMatrix />

      <section className="rounded-lg border border-border bg-surface-raised p-4">
        <h2 className="text-sm font-semibold">Optional network paths</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {networkPaths.map((path) => (
            <article className="rounded-lg border border-border bg-surface p-4" key={path.title}>
              <div className="flex items-start gap-3">
                <path.icon className="mt-0.5 h-4 w-4 text-accent" />
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-semibold">{path.title}</h3>
                    <Badge>{path.status}</Badge>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-text-secondary">{path.data}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-3 md:grid-cols-3">
        <TrustPrinciple title="Local first" body="Core scans run against storage you add and build results locally." />
        <TrustPrinciple title="Review before cleanup" body="Cleanup flows should preview files and keep restore manifests." />
        <TrustPrinciple title="Provider limits visible" body="Connector capability and maturity should be visible before use." />
      </section>
    </section>
  )
}

function TrustPrinciple({ body, title }: { body: string; title: string }) {
  return (
    <article className="rounded-lg border border-border bg-surface-raised p-4">
      <h2 className="text-sm font-semibold">{title}</h2>
      <p className="mt-2 text-xs leading-5 text-text-secondary">{body}</p>
    </article>
  )
}
