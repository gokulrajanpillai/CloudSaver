import { listen } from '@tauri-apps/api/event'
import { open } from '@tauri-apps/plugin-shell'
import { useApi } from '@/hooks/useApi'
import { setKeyringValue } from '@/lib/keyring'

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
  if (!response.ok) {
    throw new Error('Unable to load Google Drive account details')
  }
  return response.json() as Promise<DriveAboutResponse>
}

export function useGoogleAuth() {
  const api = useApi()

  async function connectGoogleDrive(): Promise<{
    email: string
    accessToken: string
    refreshToken: string
  }> {
    const { url, state } = await api.get<AuthUrlResponse>('/auth/gdrive/url')
    await open(url)

    const callbackUrl = await new Promise<string>((resolve, reject) => {
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
      })
    })

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
