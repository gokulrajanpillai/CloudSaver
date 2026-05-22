import { useEffect } from 'react'
import { isTauri } from '@/lib/platform'
import { ScanJob, ScanResult, useStore } from '@/store'

interface ScanSocketMessage {
  id?: string
  status?: ScanJob['status']
  source_id?: string
  sourceId?: string
  stage?: string
  files_scanned?: number
  current_path?: string
  progress?: number
  result?: ScanResult
  error?: string
  notify?: boolean
  notification_body?: string
}

export function useScanSocket(jobId: string | null) {
  const sidecarPort = useStore((state) => state.sidecarPort)
  const updateScanJob = useStore((state) => state.updateScanJob)
  const updateSource = useStore((state) => state.updateSource)
  const setScanResult = useStore((state) => state.setScanResult)

  useEffect(() => {
    if (!sidecarPort || !jobId) return

    const socket = new WebSocket(`ws://127.0.0.1:${sidecarPort}/scan/${jobId}/ws`)
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data) as ScanSocketMessage
      const existingJob = useStore.getState().scanJobs[jobId]
      const sourceId = message.sourceId ?? message.source_id ?? existingJob?.sourceId ?? ''
      updateScanJob(jobId, {
        id: jobId,
        sourceId,
        status: message.status,
        stage: message.stage,
        filesScanned: message.files_scanned,
        currentPath: message.current_path,
        progress: message.progress,
        result: message.result,
        error: message.error,
      })
      if (message.status === 'complete' && message.result && sourceId) {
        setScanResult(sourceId, message.result)
        updateSource(sourceId, {
          status: 'ready',
          lastScanned: new Date().toISOString(),
          fileCount: message.result.files.length,
          quota: message.result.quota,
          totalBytes: Number(
            (message.result.audit?.summary as { total_bytes?: number } | undefined)?.total_bytes ?? 0,
          ),
        })
        // Tauri-only: fire a native event so other listeners can react
        if (isTauri() && message.notify && message.notification_body) {
          import('@tauri-apps/api/event')
            .then(({ emit }) => emit('scan-complete-notify', message.notification_body))
            .catch(() => undefined)
        }
      }
      if (message.status === 'failed' && sourceId) {
        updateSource(sourceId, { status: 'error', errorMessage: message.error })
      }
    }

    return () => socket.close()
  }, [jobId, setScanResult, sidecarPort, updateScanJob, updateSource])
}
