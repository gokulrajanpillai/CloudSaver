import { RotateCcw, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { useApi } from '@/hooks/useApi'
import { useStore } from '@/store'

export function Cleanup() {
  const api = useApi()
  const batches = useStore((state) => state.reviewBatches)
  const removeReviewBatch = useStore((state) => state.removeReviewBatch)
  const [confirmBatch, setConfirmBatch] = useState<string | null>(null)
  const [confirmText, setConfirmText] = useState('')

  async function restore(manifestPath: string, batchId: string) {
    await api.post('/cleanup/restore', { manifest_path: manifestPath })
    removeReviewBatch(batchId)
  }

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'z' && batches[0]) {
        event.preventDefault()
        void restore(batches[0].manifestPath, batches[0].id)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [batches])

  return (
    <section className="space-y-4">
      <h1 className="text-lg font-semibold">Cleanup Queue</h1>
      <div className="space-y-3">
        {batches.map((batch) => (
          <article className="rounded-lg border border-border bg-surface-raised p-4" key={batch.id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="text-sm font-semibold">
                  {batch.sourceLabel} — {batch.fileCount} files
                </div>
                <div className="mt-1 break-all text-xs text-text-muted">{batch.manifestPath}</div>
                <div className="mt-1 text-xs text-text-secondary">
                  moved {new Date(batch.createdAt).toLocaleString()}
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={() => void restore(batch.manifestPath, batch.id)} size="sm" type="button" variant="outline">
                  <RotateCcw className="h-3.5 w-3.5" />
                  Restore
                </Button>
                <Button onClick={() => setConfirmBatch(batch.id)} size="sm" type="button" variant="destructive">
                  <Trash2 className="h-3.5 w-3.5" />
                  Delete permanently
                </Button>
              </div>
            </div>
            {confirmBatch === batch.id && (
              <div className="mt-4 rounded-md border border-destructive/40 bg-surface p-3">
                <p className="text-sm">
                  These {batch.fileCount} files will be permanently deleted. This cannot be undone.
                </p>
                <input
                  className="mt-3 h-9 w-full rounded-md border border-border bg-surface px-3 text-sm"
                  onChange={(event) => setConfirmText(event.target.value)}
                  placeholder="Type delete to confirm"
                  value={confirmText}
                />
                <Button
                  className="mt-3"
                  disabled={confirmText !== 'delete'}
                  onClick={() => {
                    removeReviewBatch(batch.id)
                    setConfirmBatch(null)
                    setConfirmText('')
                  }}
                  size="sm"
                  type="button"
                  variant="destructive"
                >
                  Confirm delete
                </Button>
              </div>
            )}
          </article>
        ))}
        {!batches.length && (
          <p className="rounded-lg border border-border bg-surface-raised p-4 text-sm text-text-muted">
            No review batches yet.
          </p>
        )}
      </div>
    </section>
  )
}
