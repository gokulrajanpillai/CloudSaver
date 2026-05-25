import { ShieldCheck } from 'lucide-react'
import { PRODUCT_CONTRACT } from '@/lib/product-contract'

export function ProductContract() {
  return (
    <section className="rounded-lg border border-border bg-surface-raised p-4" aria-label="Product contract">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-accent/10">
          <ShieldCheck className="h-5 w-5 text-accent" />
        </div>
        <div className="min-w-0">
          <h2 className="text-sm font-semibold">Product contract</h2>
          <p className="mt-1 text-sm text-text-secondary">{PRODUCT_CONTRACT.promise}</p>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <ContractList title="CloudSaver does" items={PRODUCT_CONTRACT.does} />
            <ContractList title="CloudSaver does not" items={PRODUCT_CONTRACT.doesNot} />
          </div>
        </div>
      </div>
    </section>
  )
}

function ContractList({ items, title }: { items: string[]; title: string }) {
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-text-muted">{title}</h3>
      <ul className="mt-2 space-y-1.5 text-xs text-text-secondary">
        {items.map((item) => (
          <li className="flex gap-2" key={item}>
            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
