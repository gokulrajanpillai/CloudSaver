import { Cloud, Folder, HardDrive, MoreHorizontal, Play } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatBytes, relativeTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { Source } from '@/types'

export function SourceCard({
  source,
  onRemove,
  onScan,
}: {
  source: Source
  onRemove?: () => void
  onScan?: () => void
}) {
  const quotaPercent = source.quota?.total
    ? Math.min(100, Math.round((source.quota.used / source.quota.total) * 100))
    : 0
  const Icon = source.type === 'icloud' ? Cloud : source.type === 'google_drive' ? HardDrive : Folder

  return (
    <article className="rounded-lg border border-border bg-surface-raised p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-surface-overlay">
            <Icon className="h-5 w-5 text-accent" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="truncate text-sm font-semibold">{source.label}</h3>
              <Badge>{source.type.replace('_', ' ')}</Badge>
            </div>
            <p className="mt-1 truncate text-xs text-text-muted">
              {source.path || source.driveAccountEmail || 'No path'}
            </p>
            <p className="mt-2 text-xs text-text-secondary">
              {formatBytes(source.totalBytes)} · {source.fileCount ?? 0} files
            </p>
          </div>
        </div>
        <Button aria-label="Source menu" onClick={onRemove} size="icon" type="button" variant="ghost">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </div>

      {source.quota && (
        <div className="mt-3">
          <div className="mb-1 flex justify-between text-xs text-text-muted">
            <span>{formatBytes(source.quota.used)} used</span>
            <span>{formatBytes(source.quota.total)} total</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-border">
            <div
              className={cn(
                'h-full rounded-full transition-all',
                quotaPercent > 90
                  ? 'bg-destructive'
                  : quotaPercent > 75
                    ? 'bg-warning'
                    : 'bg-accent',
              )}
              style={{ width: `${quotaPercent}%` }}
            />
          </div>
          {quotaPercent > 90 && (
            <p className="mt-1 text-xs text-destructive">
              Storage nearly full — scan to find what to remove
            </p>
          )}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between gap-3">
        <span className="text-xs text-text-muted">{relativeTime(source.lastScanned)}</span>
        <Button disabled={source.status === 'scanning'} onClick={onScan} size="sm" type="button">
          <Play className="h-3.5 w-3.5" />
          Scan now
        </Button>
      </div>
    </article>
  )
}
