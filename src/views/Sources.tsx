import { ChevronDown, FolderPlus, HardDrive } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { ProviderLimitations } from '@/components/ProviderLimitations'
import { SourceCard } from '@/components/SourceCard'
import { Button } from '@/components/ui/button'
import { useApi } from '@/hooks/useApi'
import { useGoogleAuth } from '@/hooks/useGoogleAuth'
import { useScanSocket } from '@/hooks/useScanSocket'
import { isTauri, openDirectory, pathsFromDrop, showNotification } from '@/lib/platform'
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
  const { connectGoogleDrive } = useGoogleAuth()
  const sources = useStore((state) => state.sources)
  const scanJobs = useStore((state) => state.scanJobs)
  const sidecarReady = useStore((state) => state.sidecarReady)
  const addSource = useStore((state) => state.addSource)
  const removeSource = useStore((state) => state.removeSource)
  const updateSource = useStore((state) => state.updateSource)
  const updateScanJob = useStore((state) => state.updateScanJob)
  const [detected, setDetected] = useState<DetectedSource[]>([])
  const [menuOpen, setMenuOpen] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [connectingDrive, setConnectingDrive] = useState(false)

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

  function addLocalSource(path: string, type: SourceType = 'local', label?: string) {
    if (sources.some((source) => source.path === path)) return
    const parts = path.split(/[\\/]/).filter(Boolean)
    addSource({
      id: crypto.randomUUID(),
      type,
      label: label || parts[parts.length - 1] || path,
      path,
      status: 'idle',
    })
  }

  function addDetectedSource(candidate: DetectedSource) {
    addLocalSource(candidate.path, candidate.type, candidate.label)
  }

  async function addLocalFolder() {
    const selected = await openDirectory()
    if (!selected) return
    addLocalSource(selected)
    setMenuOpen(false)
  }

  // Tauri: native drag-drop event carries full paths
  useEffect(() => {
    if (!isTauri()) return
    let dispose: (() => void) | undefined

    import('@tauri-apps/api/event').then(({ listen }) => {
      listen<{ paths: string[] }>('tauri://drag-drop', (event) => {
        event.payload.paths.forEach((path) => addLocalSource(path))
        setDragOver(false)
      }).then((fn) => { dispose = fn })
    }).catch(() => undefined)

    return () => dispose?.()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sources])

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

  async function addGoogleDrive() {
    setConnectingDrive(true)
    try {
      const account = await connectGoogleDrive()
      addSource({
        id: crypto.randomUUID(),
        type: 'google_drive',
        label: `Google Drive (${account.email})`,
        driveAccountEmail: account.email,
        accessToken: account.accessToken,
        status: 'idle',
      })
      setMenuOpen(false)
    } finally {
      setConnectingDrive(false)
    }
  }

  useEffect(() => {
    Object.values(scanJobs).forEach((job) => {
      if (job.status === 'complete' && job.result) {
        showNotification(
          'CloudSaver scan complete',
          `${job.sourceName || 'Source'} · ${job.result.files.length} files scanned`,
        )
      }
    })
  }, [scanJobs])

  function handleDrop(event: React.DragEvent<HTMLElement>) {
    event.preventDefault()
    setDragOver(false)
    if (isTauri()) return // Tauri handles this via the native event listener above
    const paths = pathsFromDrop(event.nativeEvent)
    paths.forEach((p) => addLocalSource(p))
  }

  return (
    <section
      className="space-y-6"
      onDragLeave={() => setDragOver(false)}
      onDragOver={(event) => {
        event.preventDefault()
        setDragOver(true)
      }}
      onDrop={handleDrop}
    >
      {activeJobIds.map((jobId) => (
        <ScanWatcher jobId={jobId} key={jobId} />
      ))}
      <div className="flex items-center justify-between gap-3 border-b border-border pb-4">
        <h1 className="text-lg font-semibold">Sources</h1>
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
                className="w-full rounded px-3 py-2 text-left text-sm hover:bg-surface-overlay disabled:text-text-muted"
                disabled={connectingDrive}
                onClick={() => void addGoogleDrive()}
                type="button"
              >
                {connectingDrive ? 'Opening Google sign-in...' : 'Google Drive...'}
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
      <ProviderLimitations />

      <div>
        <h2 className="mb-3 text-sm font-semibold text-text-secondary">Suggested — not yet added</h2>
        <div
          className={[
            'mb-3 min-h-20 rounded-lg border-2 transition-colors',
            dragOver ? 'border-dashed border-accent bg-accent/5' : 'border-border bg-surface-raised',
          ].join(' ')}
        >
          {dragOver && (
            <p className="p-6 text-center text-sm text-text-muted">Drop folder to add as source</p>
          )}
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {suggested.slice(0, 6).map((source) => (
            <button
              className="rounded-lg border border-border bg-surface-raised p-4 text-left transition-colors hover:border-accent hover:bg-surface-overlay"
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
            <div className="col-span-2 flex flex-col items-center rounded-lg border border-dashed border-border bg-surface-raised px-6 py-12 text-center">
              <HardDrive className="h-10 w-10 text-text-muted" />
              <h3 className="mt-4 text-sm font-semibold">No sources connected</h3>
              <p className="mt-1 max-w-xs text-xs text-text-muted">Add a local folder or cloud account to start scanning. CloudSaver will find duplicates and calculate your storage costs.</p>
              <Button className="mt-5" onClick={() => setMenuOpen(true)} type="button">
                <FolderPlus className="h-4 w-4" />
                Add your first source
              </Button>
            </div>
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
