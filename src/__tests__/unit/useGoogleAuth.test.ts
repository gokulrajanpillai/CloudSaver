import { renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useGoogleAuth } from '@/hooks/useGoogleAuth'
import { useStore } from '@/store'

// ---------------------------------------------------------------------------
// Shared mocks
// ---------------------------------------------------------------------------

const mockApi = {
  get: vi.fn(),
  post: vi.fn(),
  delete: vi.fn(),
  sidecarPort: 8765,
}

vi.mock('@/hooks/useApi', () => ({
  useApi: () => mockApi,
}))

// Mock setKeyringValue to be a no-op
vi.mock('@/lib/keyring', () => ({
  setKeyringValue: vi.fn().mockResolvedValue(undefined),
}))

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const AUTH_URL_RESPONSE = { url: 'https://accounts.google.com/o/oauth2/auth?...', state: 'test-state-123' }
const TOKEN_RESPONSE = { access_token: 'at-abc', refresh_token: 'rt-xyz', expires_in: 3600 }
const DRIVE_ABOUT = { user: { emailAddress: 'user@example.com' } }

beforeEach(() => {
  vi.clearAllMocks()
  useStore.setState({ sidecarPort: 8765, sidecarReady: true })
})

describe('useGoogleAuth — browser popup path', () => {
  beforeEach(() => {
    // Ensure isTauri() returns false (no __TAURI_INTERNALS__)
    const saved = window.__TAURI_INTERNALS__
    // @ts-expect-error force browser mode
    delete window.__TAURI_INTERNALS__
    return () => { window.__TAURI_INTERNALS__ = saved }
  })

  it('opens a popup window with the auth URL', async () => {
    mockApi.get.mockResolvedValue(AUTH_URL_RESPONSE)
    mockApi.post.mockResolvedValue(TOKEN_RESPONSE)

    const popup = {
      closed: false,
      location: { href: 'about:blank' },
      close: vi.fn(),
    }
    const openSpy = vi.fn().mockReturnValue(popup)
    vi.stubGlobal('open', openSpy)

    // Simulate popup navigating to callback URL
    const callbackUrl = `http://localhost:1420/auth/callback?code=authcode123&state=test-state-123`
    vi.spyOn(global, 'fetch').mockImplementationOnce(async () => ({
      ok: true,
      json: async () => DRIVE_ABOUT,
    } as Response))

    // Simulate popup arriving at callback during the poll interval
    setTimeout(() => {
      popup.location.href = callbackUrl
    }, 100)

    const { result } = renderHook(() => useGoogleAuth())
    const account = await result.current.connectGoogleDrive()

    expect(openSpy).toHaveBeenCalledWith(AUTH_URL_RESPONSE.url, 'google-oauth', expect.any(String))
    expect(account.email).toBe('user@example.com')
    expect(account.accessToken).toBe('at-abc')
    expect(account.refreshToken).toBe('rt-xyz')

    vi.unstubAllGlobals()
  })

  it('rejects when auth URL fetch fails', async () => {
    mockApi.get.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useGoogleAuth())
    await expect(result.current.connectGoogleDrive()).rejects.toThrow('Network error')
  })
})

describe('useGoogleAuth — state mismatch', () => {
  it('throws when returned state does not match', async () => {
    mockApi.get.mockResolvedValue({ url: 'https://accounts.google.com/...', state: 'original-state' })

    const popup = {
      closed: false,
      location: { href: 'about:blank' },
      close: vi.fn(),
    }
    vi.stubGlobal('open', vi.fn().mockReturnValue(popup))

    const saved = window.__TAURI_INTERNALS__
    // @ts-expect-error force browser mode
    delete window.__TAURI_INTERNALS__

    // Simulate popup arriving with WRONG state
    setTimeout(() => {
      popup.location.href = 'http://localhost/callback?code=abc&state=wrong-state'
    }, 100)

    const { result } = renderHook(() => useGoogleAuth())
    await expect(result.current.connectGoogleDrive()).rejects.toThrow(/state mismatch|missing code/i)

    window.__TAURI_INTERNALS__ = saved
    vi.unstubAllGlobals()
  })
})
