import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { isTauri, openUrl, pathsFromDrop, showNotification } from '@/lib/platform'

// ---------------------------------------------------------------------------
// isTauri()
// ---------------------------------------------------------------------------
describe('isTauri', () => {
  it('returns true when __TAURI_INTERNALS__ is present', () => {
    // initBrowserCompat() in setup.ts already set __TAURI_INTERNALS__
    expect(isTauri()).toBe(true)
  })

  it('returns false when __TAURI_INTERNALS__ is absent', () => {
    const saved = window.__TAURI_INTERNALS__
    // @ts-expect-error intentionally deleting to test detection
    delete window.__TAURI_INTERNALS__
    expect(isTauri()).toBe(false)
    window.__TAURI_INTERNALS__ = saved
  })
})

// ---------------------------------------------------------------------------
// openUrl()
// ---------------------------------------------------------------------------
describe('openUrl', () => {
  let windowOpen: ReturnType<typeof vi.fn>

  beforeEach(() => {
    windowOpen = vi.fn()
    vi.stubGlobal('open', windowOpen)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('calls window.open in browser mode', () => {
    const saved = window.__TAURI_INTERNALS__
    // @ts-expect-error temporarily remove to force browser path
    delete window.__TAURI_INTERNALS__
    openUrl('https://example.com')
    expect(windowOpen).toHaveBeenCalledWith('https://example.com', '_blank', 'noopener,noreferrer')
    window.__TAURI_INTERNALS__ = saved
  })
})

// ---------------------------------------------------------------------------
// showNotification()
// ---------------------------------------------------------------------------
describe('showNotification', () => {
  it('creates a Web Notification when permission is granted (browser mode)', () => {
    const saved = window.__TAURI_INTERNALS__
    // @ts-expect-error force browser path
    delete window.__TAURI_INTERNALS__

    const NotificationSpy = vi.fn() as unknown as typeof Notification & { new(...args: unknown[]): unknown }
    Object.assign(NotificationSpy, { permission: 'granted', requestPermission: vi.fn().mockResolvedValue('granted') })
    Object.defineProperty(window, 'Notification', { value: NotificationSpy, writable: true, configurable: true })

    showNotification('Test Title', 'Test Body')
    expect(NotificationSpy).toHaveBeenCalledWith('Test Title', { body: 'Test Body' })

    window.__TAURI_INTERNALS__ = saved
  })

  it('does not throw when permission is denied', () => {
    const saved = window.__TAURI_INTERNALS__
    // @ts-expect-error force browser path
    delete window.__TAURI_INTERNALS__

    Object.defineProperty(window, 'Notification', {
      value: Object.assign(vi.fn(), { permission: 'denied', requestPermission: vi.fn() }),
      writable: true,
      configurable: true,
    })

    expect(() => showNotification('Title', 'Body')).not.toThrow()

    window.__TAURI_INTERNALS__ = saved
  })
})

// ---------------------------------------------------------------------------
// pathsFromDrop()
// ---------------------------------------------------------------------------
describe('pathsFromDrop', () => {
  it('returns folder names from directory entries', () => {
    const makeEntry = (name: string, isDir: boolean) => ({
      isDirectory: isDir,
      name,
    })

    const event = {
      dataTransfer: {
        items: [
          { webkitGetAsEntry: () => makeEntry('photos', true) },
          { webkitGetAsEntry: () => makeEntry('notes.txt', false) }, // file, not dir
          { webkitGetAsEntry: () => makeEntry('documents', true) },
        ],
      },
    } as unknown as DragEvent

    const result = pathsFromDrop(event)
    expect(result).toEqual(['photos', 'documents'])
  })

  it('returns empty array when dataTransfer is absent', () => {
    const event = { dataTransfer: null } as unknown as DragEvent
    expect(pathsFromDrop(event)).toEqual([])
  })

  it('returns empty array when items is empty', () => {
    const event = { dataTransfer: { items: [] } } as unknown as DragEvent
    expect(pathsFromDrop(event)).toEqual([])
  })
})
