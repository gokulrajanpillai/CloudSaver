/**
 * Initialises Tauri IPC mocks so the app runs in a plain browser or WebView.
 * Call this once before React mounts, before any @tauri-apps imports execute.
 *
 * In a real Tauri window this is a no-op (the real IPC is already present).
 */

import { isTauri } from '@/lib/platform'

export function initBrowserCompat(): void {
  if (isTauri()) return

  const apiPort = parseInt(import.meta.env.VITE_API_PORT ?? '8765', 10)
  const apiBase = `http://127.0.0.1:${apiPort}`

  // Set up __TAURI_INTERNALS__ using the official mock helpers so all
  // downstream @tauri-apps/api imports resolve without errors.
  const callbacks = new Map<number, (data: unknown) => void>()

  function registerCallback(callback: ((data: unknown) => void) | undefined, once = false): number {
    const id = window.crypto.getRandomValues(new Uint32Array(1))[0]
    callbacks.set(id, (data) => {
      if (once) callbacks.delete(id)
      callback?.(data)
    })
    return id
  }

  async function invoke(cmd: string, args?: Record<string, unknown>): Promise<unknown> {
    // Sidecar port — return the env-configured value immediately so
    // TauriProvider marks the app as ready without waiting for a native event.
    if (cmd === 'get_sidecar_port') return apiPort

    // Keyring — no-op in browser
    if (cmd === 'plugin:keyring|get_password') return null
    if (cmd === 'plugin:keyring|set_password') return null
    if (cmd === 'plugin:keyring|delete_password') return null

    // Shell open — handled by platform.ts / window.open
    if (cmd === 'plugin:shell|open') {
      const url = (args as { path?: string } | undefined)?.path
      if (url) window.open(url, '_blank', 'noopener,noreferrer')
      return null
    }

    // Notifications — delegate to Web Notifications API
    if (cmd === 'plugin:notification|is_permission_granted') {
      return Notification.permission === 'granted'
    }
    if (cmd === 'plugin:notification|request_permission') {
      return Notification.requestPermission()
    }
    if (cmd === 'plugin:notification|notify') return null

    // Dialog open — handled by platform.ts openDirectory()
    if (cmd === 'plugin:dialog|open') return null

    // File system — not used outside Tauri context
    if (cmd.startsWith('plugin:fs|')) return null

    // HTTP plugin — proxy to fetch so any invoke-based HTTP calls still work
    if (cmd === 'plugin:http|fetch') {
      const { url, method = 'GET', headers = {}, body } = args as {
        url: string
        method?: string
        headers?: Record<string, string>
        body?: string
      }
      const res = await fetch(url.startsWith('/') ? `${apiBase}${url}` : url, {
        method,
        headers,
        body,
      })
      return { status: res.status, data: await res.text() }
    }

    // Event plugin — handled by the mock event system below
    if (cmd === 'plugin:event|listen') return registerCallback(undefined)
    if (cmd === 'plugin:event|emit') return null
    if (cmd === 'plugin:event|unlisten') return null

    return null
  }

  window.__TAURI_INTERNALS__ = {
    invoke,
    transformCallback: registerCallback,
    unregisterCallback: (id: number) => callbacks.delete(id),
    runCallback: (id: number, data: unknown) => callbacks.get(id)?.(data),
    callbacks,
    convertFileSrc: (p: string) => p,
    metadata: {
      currentWindow: { label: 'main' },
      currentWebview: { windowLabel: 'main', label: 'main' },
    },
  } as unknown as typeof window.__TAURI_INTERNALS__

  window.__TAURI_EVENT_PLUGIN_INTERNALS__ = {
    unregisterListener: (_event: string, id: number) => callbacks.delete(id),
  } as unknown as typeof window.__TAURI_EVENT_PLUGIN_INTERNALS__
}
