import { ArrowRight, Copy, HardDrive, Image, PiggyBank } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { ProductContract } from '@/components/ProductContract'
import { formatBytes } from '@/lib/format'
import { useStore } from '@/store'

export const PROVIDER_RATES: Record<string, { label: string; ratePerGBMonth: number }> = {
  google_one_100: { label: 'Google One 100 GB', ratePerGBMonth: 0.03 },
  google_one_200: { label: 'Google One 200 GB', ratePerGBMonth: 0.015 },
  icloud_50: { label: 'iCloud+ 50 GB', ratePerGBMonth: 0.02 },
  icloud_200: { label: 'iCloud+ 200 GB', ratePerGBMonth: 0.01 },
  icloud_2tb: { label: 'iCloud+ 2 TB', ratePerGBMonth: 0.005 },
  custom: { label: 'Custom', ratePerGBMonth: 0.025 },
}

export function Overview() {
  const sources = useStore((state) => state.sources)
  const scanResults = useStore((state) => state.scanResults)
  const crossSourceGroups = useStore((state) => state.crossSourceGroups)
  const duplicateGroups = useStore((state) => state.duplicateGroups)
  const setView = useStore((state) => state.setView)
  const detectedProvider = sources.some((source) => source.type === 'google_drive')
    ? 'google_one_100'
    : sources.some((source) => source.type === 'icloud')
      ? 'icloud_200'
      : 'custom'
  const [provider, setProvider] = useState(detectedProvider)

  const metrics = useMemo(() => {
    const results = Object.values(scanResults)
    const files = results.flatMap((result) => result.files)
    const totalBytes = files.reduce((total, file) => total + Number(file.size_bytes || 0), 0)
    const imageSavings = results.reduce((total, result) => {
      const opportunities = (result.audit?.opportunities || {}) as Record<string, unknown>
      return total + Number(opportunities.image_optimization_bytes || 0)
    }, 0)
    const duplicateBytes =
      crossSourceGroups.reduce((total, group) => total + Number(group.recoverableBytes || 0), 0) +
      duplicateGroups.reduce((total, group) => total + Number(group.recoverableBytes || 0), 0)
    return { totalBytes, fileCount: files.length, imageSavings, duplicateBytes }
  }, [crossSourceGroups, duplicateGroups, scanResults])

  const monthlyCost = ((metrics.totalBytes / 1024 ** 3) * PROVIDER_RATES[provider].ratePerGBMonth).toFixed(2)

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-semibold">Overview</h1>
        <Select value={provider} onChange={(event) => setProvider(event.target.value)}>
          {Object.entries(PROVIDER_RATES).map(([key, value]) => (
            <option key={key} value={key}>
              {value.label}
            </option>
          ))}
        </Select>
      </div>
      <ProductContract />

      <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
        <Metric icon={HardDrive} label="Total storage" value={formatBytes(metrics.totalBytes)} />
        <Metric icon={HardDrive} label="Total files" value={metrics.fileCount.toLocaleString()} />
        <Metric icon={Copy} label="Duplicates" value={crossSourceGroups.length.toString()} />
        <Metric icon={Image} label="Image savings" value={formatBytes(metrics.imageSavings)} />
        <Metric icon={PiggyBank} label="Monthly cost" value={`$${monthlyCost}`} />
      </div>

      {!sources.length ? (
        <div className="flex flex-col items-center rounded-lg border border-dashed border-border bg-surface-raised px-8 py-14 text-center">
          <HardDrive className="h-12 w-12 text-text-muted" />
          <h2 className="mt-5 text-base font-semibold">Scan your first source to get started</h2>
          <p className="mt-2 max-w-sm text-sm text-text-muted">Connect a local folder, iCloud Drive, or Google Drive account. CloudSaver will analyse your files, find duplicates, and show you exactly how much you can recover.</p>
          <Button className="mt-6" onClick={() => setView('sources')} type="button">
            Connect a source
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-text-secondary">Recommended Next Steps</h2>
          <div className="grid gap-3 md:grid-cols-4">
            <PlanCard
              action="Review duplicates"
              amount={metrics.duplicateBytes}
              onClick={() => setView('duplicates')}
              title="Remove extra copies"
            />
            <PlanCard
              action="Optimize images"
              amount={metrics.imageSavings}
              onClick={() => setView('cleanup')}
              title="Create reduced image copies"
            />
            <PlanCard
              action="Add sources"
              amount={0}
              onClick={() => setView('sources')}
              title="Scan more storage locations"
            />
            <PlanCard
              action="Learn how to unlock"
              amount={0}
              disabled
              onClick={() => undefined}
              title="Re-encode video and audio"
            />
          </div>
        </div>
      )}
    </section>
  )
}

function Metric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof HardDrive
  label: string
  value: string
}) {
  return (
    <div className="rounded-lg border border-border bg-surface-raised p-4">
      <Icon className="h-4 w-4 text-accent" />
      <div className="mt-3 text-xl font-semibold leading-tight">{value}</div>
      <div className="mt-1 text-xs text-text-muted leading-snug">{label}</div>
    </div>
  )
}

function PlanCard({
  action,
  amount,
  disabled,
  onClick,
  title,
}: {
  action: string
  amount: number
  disabled?: boolean
  onClick: () => void
  title: string
}) {
  return (
    <article className={`rounded-lg border p-4 ${disabled ? 'border-border bg-surface opacity-60' : 'border-border bg-surface-raised'}`}>
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="mt-2 text-xs text-text-muted">
        {disabled ? 'Requires additional setup' : amount ? `${formatBytes(amount)} available` : 'Ready when needed'}
      </p>
      <Button className="mt-4" disabled={disabled} onClick={onClick} size="sm" type="button" variant={disabled ? 'outline' : 'default'}>
        {action}
      </Button>
    </article>
  )
}
