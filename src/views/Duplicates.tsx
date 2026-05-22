import { Check, Copy, Folder, HardDrive, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { ICloudStateBadge, canRevealICloudFile } from '@/components/ICloudStateBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useApi } from '@/hooks/useApi'
import { formatBytes } from '@/lib/format'
import { cn } from '@/lib/utils'
import { useStore } from '@/store'

interface DuplicateFile {
  source_id: string
  source_type: string
  file_id: string
  name: string
  size_bytes: number
  path?: string
  drive_id?: string
  icloud_state?: string
}

export function Duplicates() {
  const api = useApi()
  const sources = useStore((state) => state.sources)
  const crossSourceGroups = useStore((state) => state.crossSourceGroups)
  const duplicateGroups = useStore((state) => state.duplicateGroups)
  const [keepByGroup, setKeepByGroup] = useState<Record<string, string>>({})

  const totalRecoverable = useMemo(
    () =>
      crossSourceGroups.reduce((total, group) => total + Number(group.recoverableBytes || 0), 0) +
      duplicateGroups.reduce((total, group) => total + Number(group.recoverableBytes || 0), 0),
    [crossSourceGroups, duplicateGroups],
  )

  async function applyGroup(groupIndex: number, files: DuplicateFile[]) {
    const groupKey = `cross-${groupIndex}`
    const keepId = keepByGroup[groupKey] || files[0]?.file_id
    const removable = files.filter(
      (file) => file.file_id !== keepId && canRevealICloudFile(file.icloud_state),
    )

    const localByRoot = removable.filter((file) => file.source_type !== 'google_drive' && file.path)
    const driveFiles = removable.filter((file) => file.source_type === 'google_drive' && file.drive_id)

    await Promise.all(
      localByRoot.map((file) =>
        api.post('/cleanup/move', {
          root_path: '/',
          file_ids: [file.path],
        }),
      ),
    )
    await Promise.all(
      driveFiles.map((file) =>
        api.post(`/gdrive/file/${file.drive_id}/trash`, {
          access_token: sources.find((source) => source.id === file.source_id)?.accessToken || '',
        }),
      ),
    )
  }

  return (
    <section className="space-y-6">
      <div className="rounded-lg border border-border bg-surface-raised p-4">
        <div className="text-sm font-semibold">
          {crossSourceGroups.length} cross-source groups · {duplicateGroups.length} local duplicate groups
        </div>
        <div className="mt-1 text-[32px] font-semibold">{formatBytes(totalRecoverable)}</div>
        <div className="text-xs text-text-muted">Total recoverable</div>
      </div>

      <section className="space-y-3">
        <header className={`pl-3 ${crossSourceGroups.length ? 'border-l-4 border-destructive' : 'border-l-4 border-border'}`}>
          <h1 className="text-lg font-semibold">Cross-Source Duplicates</h1>
          <p className="text-sm text-text-secondary">
            Found across multiple sources · {crossSourceGroups.length} groups · {formatBytes(totalRecoverable)} recoverable
          </p>
        </header>
        <div className="space-y-3">
          {crossSourceGroups.map((group, index) => {
            const files = ((group.files || []) as unknown as DuplicateFile[])
            const groupKey = `cross-${index}`
            const keepId = keepByGroup[groupKey] || files[0]?.file_id
            return (
              <article className="rounded-lg border border-border bg-surface-raised p-4" key={groupKey}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-sm font-semibold">{group.name || files[0]?.name || 'Duplicate group'}</h2>
                    <p className="text-xs text-text-muted">
                      {formatBytes(Number(group.recoverableBytes || 0))} recoverable
                    </p>
                  </div>
                  <Badge>{group.confidence || 'medium'} confidence</Badge>
                </div>
                <div className="mt-4 divide-y divide-border">
                  {files.map((file) => {
                    const source = sources.find((item) => item.id === file.source_id)
                    const isKeep = keepId === file.file_id
                    const Icon = file.source_type === 'google_drive' ? HardDrive : Folder
                    return (
                      <div className="flex items-center justify-between gap-3 py-3" key={`${file.source_id}-${file.file_id}`}>
                        <div className="flex min-w-0 items-center gap-3">
                          <Icon className="h-4 w-4 shrink-0 text-accent" />
                          <div className="min-w-0">
                            <div className="truncate text-sm">{source?.label || file.source_type}</div>
                            <div className="truncate text-xs text-text-muted">{file.path || file.name}</div>
                          </div>
                          <ICloudStateBadge state={file.icloud_state} />
                        </div>
                        <Button
                          className={cn(isKeep ? 'text-success' : 'text-destructive')}
                          disabled={file.icloud_state === 'evicted'}
                          onClick={() => setKeepByGroup((state) => ({ ...state, [groupKey]: file.file_id }))}
                          size="sm"
                          type="button"
                          variant="outline"
                        >
                          {isKeep ? <Check className="h-3.5 w-3.5" /> : <X className="h-3.5 w-3.5" />}
                          {isKeep ? 'keep' : 'remove'}
                        </Button>
                      </div>
                    )
                  })}
                </div>
                <div className="mt-4 flex items-center justify-between gap-3">
                  <span className="text-xs text-text-muted">Verified · Hash match</span>
                  <Button onClick={() => void applyGroup(index, files)} size="sm" type="button">
                    Apply
                  </Button>
                </div>
              </article>
            )
          })}
          {!crossSourceGroups.length && (
            <div className="flex flex-col items-center rounded-lg border border-dashed border-border bg-surface-raised px-6 py-10 text-center">
              <Copy className="h-8 w-8 text-text-muted" />
              <h3 className="mt-3 text-sm font-semibold">No duplicates found yet</h3>
              <p className="mt-1 max-w-xs text-xs text-text-muted">Scan at least two sources to detect files that exist in multiple places. Recoverable space will appear here.</p>
            </div>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Within-Source Exact Duplicates</h2>
        <p className="mt-2 text-sm text-text-muted">{duplicateGroups.length} groups ready for review.</p>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Visually Similar Images</h2>
        <Button className="mt-3" type="button" variant="outline">
          Find similar images
        </Button>
      </section>
    </section>
  )
}
