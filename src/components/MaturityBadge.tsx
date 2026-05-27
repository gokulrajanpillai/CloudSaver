import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export type Maturity = 'production' | 'preview' | 'beta' | 'planned'

const labelByMaturity: Record<Maturity, string> = {
  production: 'Production',
  preview: 'Preview',
  beta: 'Beta',
  planned: 'Planned',
}

const classByMaturity: Record<Maturity, string> = {
  production: 'border-success/30 bg-success/10 text-success',
  preview: 'border-warning/30 bg-warning/10 text-warning',
  beta: 'border-accent/30 bg-accent/10 text-accent',
  planned: 'bg-surface-overlay text-text-secondary',
}

export function MaturityBadge({ className, maturity }: { className?: string; maturity: Maturity }) {
  return <Badge className={cn(classByMaturity[maturity], className)}>{labelByMaturity[maturity]}</Badge>
}
