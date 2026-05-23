import '@testing-library/jest-dom'
import { afterEach, beforeEach, vi } from 'vitest'

// Provide VITE_API_PORT before any module reads import.meta.env
Object.defineProperty(import.meta, 'env', {
  value: { VITE_API_PORT: '8765', MODE: 'test', DEV: true, PROD: false, BASE_URL: '/' },
  writable: true,
  configurable: true,
})

// Stub browser APIs absent in happy-dom
if (!('Notification' in window)) {
  Object.defineProperty(window, 'Notification', {
    value: class Notification {
      static permission: NotificationPermission = 'granted'
      static requestPermission = vi.fn().mockResolvedValue('granted')
      constructor(_title: string, _opts?: NotificationOptions) {}
    },
    writable: true,
  })
}

// Provide crypto.getRandomValues (happy-dom may lack it)
if (!window.crypto?.getRandomValues) {
  Object.defineProperty(window, 'crypto', {
    value: {
      getRandomValues: (arr: Uint32Array) => {
        for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 0xffffffff)
        return arr
      },
      randomUUID: () => 'test-uuid-' + Math.random().toString(36).slice(2),
    },
    writable: true,
  })
}

// Install Tauri IPC mock so @tauri-apps/api imports don't throw
import { initBrowserCompat } from '@/lib/browser-compat'
initBrowserCompat()

// Reset Zustand store data between tests (preserve actions)
import { useStore } from '@/store'

const storeReset = {
  activeView: 'overview' as const,
  sidecarPort: null,
  sidecarReady: false,
  sources: [],
  scanJobs: {},
  scanResults: {},
  duplicateGroups: [],
  crossSourceGroups: [],
  visualGroups: [],
  reviewBatches: [],
  commandPaletteOpen: false,
  theme: 'system' as const,
}

beforeEach(() => {
  localStorage.clear()
  useStore.setState(storeReset)
})

afterEach(() => {
  vi.restoreAllMocks()
})
