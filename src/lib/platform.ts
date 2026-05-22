/**
 * Platform abstraction layer.
 * Each function detects whether we're running inside Tauri and uses the
 * appropriate native API, falling back to web equivalents in a browser or
 * WebView context.
 */

export const isTauri = (): boolean =>
  typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window

// ---------------------------------------------------------------------------
// File / directory picker
// ---------------------------------------------------------------------------

/** Opens a native folder picker. Returns the selected path, or null if cancelled. */
export async function openDirectory(): Promise<string | null> {
  if (isTauri()) {
    const { open } = await import('@tauri-apps/plugin-dialog')
    const result = await open({ directory: true, multiple: false })
    return typeof result === 'string' ? result : null
  }

  // Web fallback: showDirectoryPicker (Chrome 86+) or <input webkitdirectory>
  if ('showDirectoryPicker' in window) {
    try {
      const handle = await (window as typeof window & {
        showDirectoryPicker: () => Promise<{ name: string }>
      }).showDirectoryPicker()
      // The browser doesn't expose the full path — return the folder name
      return handle.name
    } catch {
      return null
    }
  }

  // Final fallback: hidden file input
  return new Promise((resolve) => {
    const input = document.createElement('input')
    input.type = 'file'
    ;(input as HTMLInputElement & { webkitdirectory: boolean }).webkitdirectory = true
    input.style.display = 'none'
    document.body.appendChild(input)
    input.onchange = () => {
      const name = input.files?.[0]?.webkitRelativePath?.split('/')[0] ?? null
      document.body.removeChild(input)
      resolve(name)
    }
    input.oncancel = () => {
      document.body.removeChild(input)
      resolve(null)
    }
    input.click()
  })
}

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------

export function showNotification(title: string, body: string): void {
  if (isTauri()) {
    import('@tauri-apps/plugin-notification')
      .then(({ sendNotification }) => sendNotification({ title, body }))
      .catch(() => undefined)
    return
  }

  if ('Notification' in window) {
    if (Notification.permission === 'granted') {
      new Notification(title, { body })
    } else if (Notification.permission !== 'denied') {
      void Notification.requestPermission().then((permission) => {
        if (permission === 'granted') new Notification(title, { body })
      })
    }
  }
}

// ---------------------------------------------------------------------------
// Open URL in system browser / new tab
// ---------------------------------------------------------------------------

export function openUrl(url: string): void {
  if (isTauri()) {
    import('@tauri-apps/plugin-shell')
      .then(({ open }) => open(url))
      .catch(() => window.open(url, '_blank'))
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

// ---------------------------------------------------------------------------
// Drag-drop: extract paths from a browser DragEvent
// ---------------------------------------------------------------------------

/**
 * Pulls folder/file names from a browser drag-drop event.
 * Returns an array of strings — full paths in Tauri, folder names in browser.
 */
export function pathsFromDrop(event: DragEvent): string[] {
  const paths: string[] = []
  const items = event.dataTransfer?.items
  if (!items) return paths
  for (let i = 0; i < items.length; i++) {
    const entry = items[i].webkitGetAsEntry?.()
    if (entry?.isDirectory) paths.push(entry.name)
  }
  return paths
}
