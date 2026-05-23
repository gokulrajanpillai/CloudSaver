import { describe, expect, it } from 'vitest'

// initBrowserCompat() already ran in setup.ts, so window.__TAURI_INTERNALS__ is set
describe('browser-compat: window globals', () => {
  it('sets window.__TAURI_INTERNALS__', () => {
    expect(window.__TAURI_INTERNALS__).toBeDefined()
  })

  it('sets window.__TAURI_EVENT_PLUGIN_INTERNALS__', () => {
    expect(window.__TAURI_EVENT_PLUGIN_INTERNALS__).toBeDefined()
  })

  it('exposes an invoke function', () => {
    expect(typeof window.__TAURI_INTERNALS__.invoke).toBe('function')
  })
})

describe('browser-compat: invoke()', () => {
  const invoke = (cmd: string, args?: Record<string, unknown>) =>
    window.__TAURI_INTERNALS__.invoke(cmd, args) as Promise<unknown>

  it('get_sidecar_port returns the configured port as a number', async () => {
    const port = await invoke('get_sidecar_port')
    expect(typeof port).toBe('number')
    expect(port).toBe(8765)
  })

  it('keyring get_password returns null', async () => {
    const result = await invoke('plugin:keyring|get_password', { service: 'CloudSaver', username: 'key' })
    expect(result).toBeNull()
  })

  it('keyring set_password resolves without error', async () => {
    await expect(invoke('plugin:keyring|set_password', { service: 'CloudSaver', username: 'key', password: 'val' })).resolves.toBeNull()
  })

  it('keyring delete_password resolves without error', async () => {
    await expect(invoke('plugin:keyring|delete_password', { service: 'CloudSaver', username: 'key' })).resolves.toBeNull()
  })

  it('plugin:notification|notify resolves without error', async () => {
    await expect(invoke('plugin:notification|notify')).resolves.toBeNull()
  })

  it('plugin:dialog|open resolves null', async () => {
    const result = await invoke('plugin:dialog|open')
    expect(result).toBeNull()
  })

  it('plugin:fs| commands resolve null', async () => {
    const result = await invoke('plugin:fs|read_file', { path: '/some/path' })
    expect(result).toBeNull()
  })

  it('unknown commands resolve null without throwing', async () => {
    const result = await invoke('some:unknown|command')
    expect(result).toBeNull()
  })

  it('plugin:event|emit resolves null', async () => {
    const result = await invoke('plugin:event|emit', { event: 'test', payload: null })
    expect(result).toBeNull()
  })

  it('plugin:event|unlisten resolves null', async () => {
    const result = await invoke('plugin:event|unlisten', { event: 'test', eventId: 1 })
    expect(result).toBeNull()
  })
})

describe('browser-compat: transformCallback', () => {
  it('registerCallback returns a number id', () => {
    const id = window.__TAURI_INTERNALS__.transformCallback(() => {})
    expect(typeof id).toBe('number')
  })
})
