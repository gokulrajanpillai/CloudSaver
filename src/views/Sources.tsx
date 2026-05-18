import { open } from '@tauri-apps/plugin-dialog'
import { sendNotification } from '@tauri-apps/plugin-notification'
import { ChevronDown, FolderPlus } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { SourceCard } from '@/components/SourceCard'
import { Button } from '@/components/ui/button'
import { useApi } from '@/hooks/useApi'
import { useScanSocket } from '@/hooks/useScanSocket'
import { useStore } from '@/store'
import type { Source, SourceType } from '@/types'

interface DetectedSource {
  type: SourceType
  label: string
  path: string
}

interface ScanStartResponse {
  job_id: string
  status: 'queued'
}

export function Sources() {
  const api = useApi()
  const sources = useStore((state) => state.sources)
  const scanJobs = useStore((state) => state.scanJobs)
  const sidecarReady = useStore((state) => state.sidecarReady)
  const addSource = useStore((state) => state.addSource)
  const removeSource = useStore((state) => state.removeSource)
  const updateSource = useStore((state) => state.updateSource)
  const updateScanJob = useStore((state) => state.updateScanJob)
  const [detected, setDetected] = useState<DetectedSource[]>([])
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    if (!sidecarReady) return
    api
      .get<{ sources: DetectedSource[] }>('/sources/detected')
      .then((response) => setDetected(response.sources))
      .catch(() => setDetected([]))
  }, [api, sidecarReady])

  const activeJobIds = useMemo(
    () =>
      Object.values(scanJobs)
        .filter((job) => job.status === 'queued' || job.status === 'scanning')
        .map((job) => job.id),
    [scanJobs],
  )

  const suggested = detected.filter(
    (candidate) => !sources.some((source) => source.path === candidate.path),
  )

  function addDetectedSource(candidate: DetectedSource) {
    addSource({
      id: crypto.randomUUID(),
      type: candidate.type,
      label: candidate.label,
      path: candidate.path,
      status: 'idle',
    })
  }

  async function addLocalFolder() {
    const selected = await open({ directory: true, multiple: false })
    if (typeof selected !== 'string') return
    const parts = selected.split(/[\\/]/).filter(Boolean)
    const label = parts[parts.length - 1] || selected
    addSource({
      id: crypto.randomUUID(),
      type: 'local',
      label,
      path: selected,
      status: 'idle',
    })
    setMenuOpen(false)
  }

  async function scanSource(source: Source) {
    if (!source.path) return
    updateSource(source.id, { status: 'scanning', errorMessage: undefined })
    const response = await api.post<ScanStartResponse>('/scan/local/start', { path: source.path })
    updateScanJob(response.job_id, {
      id: response.job_id,
      sourceId: source.id,
      sourceName: source.label,
      status: response.status,
      stage: 'Waiting',
      filesScanned: 0,
      currentPath: '',
      progress: 0,
    })
  }

  useEffect(() => {
    Object.values(scanJobs).forEach((job) => {
      if (job.status === 'complete' && job.result) {
        sendNotification({
          title: 'CloudSaver scan complete',
          body: `${job.sourceName || 'Source'} · ${job.result.files.length} files scanned`,
        })
      }
    })
  }, [scanJobs])

  return (
    <section className="space-y-6">
      {activeJobIds.map((jobId) => (
        <ScanWatcher jobId={jobId} key={jobId} />
      ))}
      <div className="flex items-center justify-between gap-3 border-b border-border pb-4">
        <h1 className="text-[18px] font-semibold">Sources</h1>
        <div className="relative">
          <Button onClick={() => setMenuOpen((open) => !open)} type="button">
            <FolderPlus className="h-4 w-4" />
            Add Source
            <ChevronDown className="h-4 w-4" />
          </Button>
          {menuOpen && (
            <div className="absolute right-0 z-20 mt-2 w-56 rounded-md border border-border bg-surface p-1 shadow-lg">
              <button
                className="w-full rounded px-3 py-2 text-left text-sm hover:bg-surface-overlay"
                onClick={addLocalFolder}
                type="button"
              >
                Local Folder...
              </button>
              <button
                className="w-full rounded px-3 py-2 text-left text-sm text-text-muted"
                disabled
                type="button"
              >
                Google Drive...
              </button>
              <button
                className="w-full rounded px-3 py-2 text-left text-sm hover:bg-surface-overlay disabled:text-text-muted"
                disabled={!detected.some((source) => source.type === 'icloud')}
                onClick={() => {
                  const icloud = detected.find((source) => source.type === 'icloud')
                  if (icloud) addDetectedSource(icloud)
                  setMenuOpen(false)
                }}
                type="button"
              >
                iCloud Drive
              </button>
            </div>
          )}
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text-secondary">Suggested — not yet added</h2>
        <div className="grid gap-3 md:grid-cols-3">
          {suggested.slice(0, 6).map((source) => (
            <button
              className="rounded-lg border border-dashed border-border bg-surface-raised p-4 text-left hover:border-accent"
              key={source.path}
              onClick={() => addDetectedSource(source)}
              type="button"
            >
              <div className="text-sm font-medium">{source.label}</div>
              <div className="mt-1 truncate text-xs text-text-muted">{source.path}</div>
            </button>
          ))}
          {!suggested.length && (
            <p className="rounded-lg border border-border bg-surface-raised p-4 text-sm text-text-muted">
              No suggested sources detected yet.
            </p>
          )}
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text-secondary">Connected sources</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {sources.map((source) => (
            <SourceCard
              key={source.id}
              onRemove={() => removeSource(source.id)}
              onScan={() => void scanSource(source)}
              source={source}
            />
          ))}
          {!sources.length && (
            <p className="rounded-lg border border-border bg-surface-raised p-4 text-sm text-text-muted">
              Add a folder or detected cloud source to start scanning.
            </p>
          )}
        </div>
      </div>
    </section>
  )
}

function ScanWatcher({ jobId }: { jobId: string }) {
  useScanSocket(jobId)
  return null
}
