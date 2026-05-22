import { useApi } from '@/hooks/useApi'
import { setKeyringValue } from '@/lib/keyring'
import { isTauri, openUrl } from '@/lib/platform'

interface AuthUrlResponse {
  url: string
  state: string
}

interface TokenResponse {
  access_token: string
  refresh_token?: string
  expires_in?: number
}

interface DriveAboutResponse {
  user: {
    emailAddress: string
  }
}

async function fetchDriveAbout(accessToken: string): Promise<DriveAboutResponse> {
  const response = await fetch(
    'https://www.googleapis.com/drive/v3/about?fields=user(emailAddress)',
    {
      headers: { Authorization: `Bearer ${accessToken}` },
    },
  )
  if (!response.ok) throw new Error('Unable to load Google Drive account details')
  return response.json() as Promise<DriveAboutResponse>
}

/** Wait for the OAuth callback via a Tauri native event. */
async function waitForCallbackTauri(): Promise<string> {
  const { listen } = await import('@tauri-apps/api/event')
  return new Promise<string>((resolve, reject) => {
    let dispose: (() => void) | undefined
    const timeout = window.setTimeout(() => {
      dispose?.()
      reject(new Error('Auth timeout'))
    }, 120_000)

    listen<string>('oauth-callback', (event) => {
      window.clearTimeout(timeout)
      dispose?.()
      resolve(event.payload)
    }).then((unlisten) => {
      dispose = unlisten
    }).catch(reject)
  })
}

/**
 * Browser fallback: listen for a postMessage from the OAuth popup.
 * The Python backend's /auth/gdrive/callback page should post the full
 * redirect URL to window.opener so we can extract the code from it.
 * Falls back to prompting the user to paste the URL if no message arrives.
 */
async function waitForCallbackBrowser(popup: Window | null): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    const timeout = window.setTimeout(() => {
      cleanup()
      // Last resort: ask user to paste the redirect URL
      const url = window.prompt(
        'Paste the redirect URL from the browser to complete Google sign-in:',
      )
      if (url) resolve(url)
      else reject(new Error('Auth cancelled'))
    }, 120_000)

    function onMessage(event: MessageEvent) {
      // Accept postMessage from any origin since redirect comes from Google
      const data = event.data as { type?: string; url?: string }
      if (data?.type === 'oauth-callback' && typeof data.url === 'string') {
        cleanup()
        resolve(data.url)
      }
    }

    // Also poll whether the popup navigated to our callback URL
    const pollInterval = window.setInterval(() => {
      try {
        if (!popup || popup.closed) {
          cleanup()
          reject(new Error('Auth popup closed'))
          return
        }
        const href = popup.location.href
        if (href.includes('code=')) {
          cleanup()
          popup.close()
          resolve(href)
        }
      } catch {
        // Cross-origin access throws until redirected back to our origin
      }
    }, 500)

    function cleanup() {
      window.clearTimeout(timeout)
      window.clearInterval(pollInterval)
      window.removeEventListener('message', onMessage)
    }

    window.addEventListener('message', onMessage)
  })
}

export function useGoogleAuth() {
  const api = useApi()

  async function connectGoogleDrive(): Promise<{
    email: string
    accessToken: string
    refreshToken: string
  }> {
    const { url, state } = await api.get<AuthUrlResponse>('/auth/gdrive/url')

    let callbackUrl: string

    if (isTauri()) {
      openUrl(url)
      callbackUrl = await waitForCallbackTauri()
    } else {
      const popup = window.open(url, 'google-oauth', 'width=520,height=640,noopener=no')
      callbackUrl = await waitForCallbackBrowser(popup)
    }

    const parsed = new URL(callbackUrl)
    const code = parsed.searchParams.get('code')
    const returnedState = parsed.searchParams.get('state')
    if (!code || returnedState !== state) {
      throw new Error('OAuth callback missing code or state mismatch')
    }

    const tokens = await api.post<TokenResponse>('/auth/gdrive/exchange', { code, state })
    if (tokens.refresh_token) {
      await setKeyringValue(`gdrive-refresh-${state}`, tokens.refresh_token)
    }

    const about = await fetchDriveAbout(tokens.access_token)
    return {
      email: about.user.emailAddress,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token || '',
    }
  }

  return { connectGoogleDrive }
}
