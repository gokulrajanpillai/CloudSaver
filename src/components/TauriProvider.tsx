import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { createContext, useContext, useEffect, type ReactNode } from 'react'
import { isTauri } from '@/lib/platform'
import { useStore } from '@/store'

const TauriContext = createContext<{ sidecarPort: number | null; ready: boolean }>({
  sidecarPort: null,
  ready: false,
})

export function TauriProvider({ children }: { children: ReactNode }) {
  const sidecarPort = useStore((state) => state.sidecarPort)
  const sidecarReady = useStore((state) => state.sidecarReady)
  const setSidecarPort = useStore((state) => state.setSidecarPort)

  useEffect(() => {
    // In browser mode the mock IPC returns the port from VITE_API_PORT directly.
    // In Tauri mode the real sidecar may not be ready yet, so also listen for
    // the sidecar-ready event as a secondary signal.
    invoke<number>('get_sidecar_port')
      .then(setSidecarPort)
      .catch(() => {
        // Outside Tauri and no mock — try the env var as a last resort
        if (!isTauri()) {
          const port = parseInt(import.meta.env.VITE_API_PORT ?? '8765', 10)
          setSidecarPort(port)
        }
      })

    if (!isTauri()) return

    const unlisten = listen<number>('sidecar-ready', (event) => {
      setSidecarPort(event.payload)
    })

    return () => {
      void unlisten.then((dispose) => dispose())
    }
  }, [setSidecarPort])

  return (
    <TauriContext.Provider value={{ sidecarPort, ready: sidecarReady }}>
      {children}
    </TauriContext.Provider>
  )
}

export function useTauri() {
  return useContext(TauriContext)
}
