/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_PORT?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Tauri internals — present in a Tauri window, absent in a browser.
// Typed loosely so both real and mocked forms satisfy the declaration.
interface Window {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  __TAURI_INTERNALS__: any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  __TAURI_EVENT_PLUGIN_INTERNALS__: any
}
