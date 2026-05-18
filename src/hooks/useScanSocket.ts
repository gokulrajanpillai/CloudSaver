import { useEffect } from 'react'
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
}

export function useScanSocket(jobId: string | null) {
  const sidecarPort = useStore((state) => state.sidecarPort)
  const updateScanJob = useStore((state) => state.updateScanJob)
  const setScanResult = useStore((state) => state.setScanResult)

  useEffect(() => {
    if (!sidecarPort || !jobId) return

    const socket = new WebSocket(`ws://127.0.0.1:${sidecarPort}/scan/${jobId}/ws`)
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data) as ScanSocketMessage
      const sourceId = message.sourceId ?? message.source_id ?? ''
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
      }
    }

    return () => socket.close()
  }, [jobId, setScanResult, sidecarPort, updateScanJob])
}
