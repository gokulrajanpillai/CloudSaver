import { renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { useApi } from '@/hooks/useApi'
import { useStore } from '@/store'

function setupPort(port: number | null) {
  useStore.setState({ sidecarPort: port, sidecarReady: port !== null })
}

describe('useApi — URL construction', () => {
  it('rejects when sidecarPort is null', async () => {
    setupPort(null)
    const { result } = renderHook(() => useApi())
    await expect(result.current.get('/health')).rejects.toThrow('Sidecar is not ready')
  })

  it('exposes the current sidecarPort', () => {
    setupPort(8765)
    const { result } = renderHook(() => useApi())
    expect(result.current.sidecarPort).toBe(8765)
  })
})

describe('useApi — get()', () => {
  it('fetches and returns parsed JSON', async () => {
    setupPort(8765)
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'ok' }),
    })
    vi.stubGlobal('fetch', fetchSpy)

    const { result } = renderHook(() => useApi())
    const data = await result.current.get<{ status: string }>('/health')

    expect(fetchSpy).toHaveBeenCalledWith('http://127.0.0.1:8765/health')
    expect(data).toEqual({ status: 'ok' })
  })

  it('throws on non-ok response', async () => {
    setupPort(8765)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      text: () => Promise.resolve('Not found'),
    }))

    const { result } = renderHook(() => useApi())
    await expect(result.current.get('/missing')).rejects.toThrow('Not found')
  })
})

describe('useApi — post()', () => {
  it('sends POST with JSON body', async () => {
    setupPort(8765)
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ job_id: 'abc', status: 'queued' }),
    })
    vi.stubGlobal('fetch', fetchSpy)

    const { result } = renderHook(() => useApi())
    const data = await result.current.post('/scan/local/start', { path: '/tmp' })

    const [url, opts] = fetchSpy.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('http://127.0.0.1:8765/scan/local/start')
    expect(opts.method).toBe('POST')
    expect(opts.headers).toMatchObject({ 'Content-Type': 'application/json' })
    expect(JSON.parse(opts.body as string)).toEqual({ path: '/tmp' })
    expect(data).toEqual({ job_id: 'abc', status: 'queued' })
  })

  it('throws on non-ok POST response', async () => {
    setupPort(8765)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      text: () => Promise.resolve('Validation error'),
    }))

    const { result } = renderHook(() => useApi())
    await expect(result.current.post('/scan/local/start', {})).rejects.toThrow('Validation error')
  })
})

describe('useApi — delete()', () => {
  it('sends DELETE request', async () => {
    setupPort(8765)
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'deleted' }),
    })
    vi.stubGlobal('fetch', fetchSpy)

    const { result } = renderHook(() => useApi())
    await result.current.delete('/sources/src-1')

    const [url, opts] = fetchSpy.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('http://127.0.0.1:8765/sources/src-1')
    expect(opts.method).toBe('DELETE')
  })
})
