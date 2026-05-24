import { renderHook } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { useApi } from '@/hooks/useApi'
import { useStore } from '@/store'

const PORT = 8765
const BASE = `http://127.0.0.1:${PORT}`

const server = setupServer()

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

function setupApi() {
  useStore.setState({ sidecarPort: PORT, sidecarReady: true })
  return renderHook(() => useApi()).result.current
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------
describe('GET /health', () => {
  it('returns status ok', async () => {
    server.use(http.get(`${BASE}/health`, () => HttpResponse.json({ status: 'ok' })))
    const api = setupApi()
    const data = await api.get<{ status: string }>('/health')
    expect(data.status).toBe('ok')
  })
})

// ---------------------------------------------------------------------------
// Scan lifecycle
// ---------------------------------------------------------------------------
describe('POST /scan/local/start', () => {
  it('returns job_id and status queued', async () => {
    server.use(
      http.post(`${BASE}/scan/local/start`, () =>
        HttpResponse.json({ job_id: 'job-123', status: 'queued' }),
      ),
    )
    const api = setupApi()
    const data = await api.post<{ job_id: string; status: string }>('/scan/local/start', { path: '/tmp/test' })
    expect(data.job_id).toBe('job-123')
    expect(data.status).toBe('queued')
  })

  it('throws on 400 validation error', async () => {
    server.use(
      http.post(`${BASE}/scan/local/start`, () =>
        HttpResponse.json({ detail: 'path does not exist' }, { status: 400 }),
      ),
    )
    const api = setupApi()
    await expect(api.post('/scan/local/start', { path: '/nonexistent' })).rejects.toThrow()
  })

  it('sends path in request body', async () => {
    let capturedBody: unknown
    server.use(
      http.post(`${BASE}/scan/local/start`, async ({ request }) => {
        capturedBody = await request.json()
        return HttpResponse.json({ job_id: 'j-1', status: 'queued' })
      }),
    )
    const api = setupApi()
    await api.post('/scan/local/start', { path: '/Users/me/Downloads' })
    expect(capturedBody).toEqual({ path: '/Users/me/Downloads' })
  })
})

// ---------------------------------------------------------------------------
// Sources detection
// ---------------------------------------------------------------------------
describe('GET /sources/detected', () => {
  it('returns sources array', async () => {
    server.use(
      http.get(`${BASE}/sources/detected`, () =>
        HttpResponse.json({
          sources: [
            { type: 'icloud', label: 'iCloud Drive', path: '/Users/me/Library/Mobile Documents/com~apple~CloudDocs' },
          ],
        }),
      ),
    )
    const api = setupApi()
    const data = await api.get<{ sources: Array<{ type: string }> }>('/sources/detected')
    expect(data.sources).toHaveLength(1)
    expect(data.sources[0].type).toBe('icloud')
  })
})

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
describe('GET /auth/gdrive/url', () => {
  it('returns url and state', async () => {
    server.use(
      http.get(`${BASE}/auth/gdrive/url`, () =>
        HttpResponse.json({ url: 'https://accounts.google.com/...', state: 'xyz-state' }),
      ),
    )
    const api = setupApi()
    const data = await api.get<{ url: string; state: string }>('/auth/gdrive/url')
    expect(data.url).toContain('google.com')
    expect(data.state).toBe('xyz-state')
  })
})

describe('POST /auth/gdrive/exchange', () => {
  it('sends code and state, returns tokens', async () => {
    let body: unknown
    server.use(
      http.post(`${BASE}/auth/gdrive/exchange`, async ({ request }) => {
        body = await request.json()
        return HttpResponse.json({ access_token: 'at-abc', refresh_token: 'rt-xyz', expires_in: 3600 })
      }),
    )
    const api = setupApi()
    const tokens = await api.post<{ access_token: string }>('/auth/gdrive/exchange', {
      code: 'auth-code', state: 'xyz-state',
    })
    expect(body).toMatchObject({ code: 'auth-code', state: 'xyz-state' })
    expect(tokens.access_token).toBe('at-abc')
  })
})

// ---------------------------------------------------------------------------
// Cleanup
// ---------------------------------------------------------------------------
describe('POST /cleanup/move', () => {
  it('sends root_path and file_ids', async () => {
    let body: unknown
    server.use(
      http.post(`${BASE}/cleanup/move`, async ({ request }) => {
        body = await request.json()
        return HttpResponse.json({ manifest: '/tmp/manifest.json', count: 1 })
      }),
    )
    const api = setupApi()
    await api.post('/cleanup/move', { root_path: '/', file_ids: ['/Downloads/file.jpg'] })
    expect(body).toMatchObject({ root_path: '/', file_ids: ['/Downloads/file.jpg'] })
  })
})

describe('POST /cleanup/restore', () => {
  it('sends manifest path', async () => {
    let body: unknown
    server.use(
      http.post(`${BASE}/cleanup/restore`, async ({ request }) => {
        body = await request.json()
        return HttpResponse.json({ restored: ['/Downloads/file.jpg'] })
      }),
    )
    const api = setupApi()
    await api.post('/cleanup/restore', { manifest: '/tmp/manifest.json' })
    expect(body).toMatchObject({ manifest: '/tmp/manifest.json' })
  })
})

// ---------------------------------------------------------------------------
// Duplicates
// ---------------------------------------------------------------------------
describe('POST /duplicates/cross', () => {
  it('returns groups array', async () => {
    server.use(
      http.post(`${BASE}/duplicates/cross`, () =>
        HttpResponse.json({
          groups: [{ id: 'g-1', name: 'photo.jpg', recoverableBytes: 1000, files: [] }],
        }),
      ),
    )
    const api = setupApi()
    const data = await api.post<{ groups: unknown[] }>('/duplicates/cross', { source_ids: ['s-1', 's-2'] })
    expect(data.groups).toHaveLength(1)
  })
})
