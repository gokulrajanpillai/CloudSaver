import { useMemo } from 'react'
import { useStore } from '@/store'

type JsonBody = Record<string, unknown> | Array<unknown>

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed with ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function useApi() {
  const sidecarPort = useStore((state) => state.sidecarPort)

  return useMemo(() => {
    const url = (path: string) => {
      if (!sidecarPort) {
        throw new Error('Sidecar is not ready')
      }
      return `http://127.0.0.1:${sidecarPort}${path}`
    }

    return {
      get: async <T>(path: string): Promise<T> => parseJson<T>(await fetch(url(path))),
      post: async <T>(path: string, body?: JsonBody): Promise<T> =>
        parseJson<T>(
          await fetch(url(path), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body ? JSON.stringify(body) : undefined,
          }),
        ),
      delete: async <T>(path: string): Promise<T> =>
        parseJson<T>(await fetch(url(path), { method: 'DELETE' })),
      sidecarPort,
    }
  }, [sidecarPort])
}
