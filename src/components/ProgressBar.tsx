import { useShallow } from 'zustand/react/shallow'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useStore } from '@/store'

export function ProgressBar() {
  const jobs = useStore(
    useShallow((state) =>
      Object.values(state.scanJobs).filter((job) => job.status === 'queued' || job.status === 'scanning'),
    ),
  )

  if (!jobs.length) return null

  return (
    <div className="fixed bottom-0 left-16 right-0 z-50 space-y-2 border-t border-border bg-surface p-3 shadow-lg">
      {jobs.map((job) => (
        <div key={job.id} className="grid grid-cols-[1fr_auto] items-center gap-3">
          <div>
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="font-medium">{job.sourceName || job.sourceId || 'Scanning source'}</span>
              <span className="text-xs text-text-muted">{job.filesScanned} files</span>
            </div>
            <div className="mt-1 flex items-center gap-3">
              <Progress value={job.progress ?? 0} />
              <span className="w-32 truncate text-xs text-text-muted">{job.stage}</span>
            </div>
          </div>
          <Button aria-label="Cancel scan" size="icon" type="button" variant="ghost">
            <X className="h-4 w-4" />
          </Button>
        </div>
      ))}
    </div>
  )
}
