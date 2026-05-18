import { cn } from '@/lib/utils'

export function Progress({ value = 0, className }: { value?: number; className?: string }) {
  return (
    <div className={cn('h-2 overflow-hidden rounded-full bg-border', className)}>
      <div className="h-full bg-accent transition-all" style={{ width: `${value}%` }} />
    </div>
  )
}
