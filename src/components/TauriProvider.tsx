import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { createContext, useContext, useEffect, type ReactNode } from 'react'
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
    invoke<number>('get_sidecar_port')
      .then(setSidecarPort)
      .catch(() => undefined)

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
