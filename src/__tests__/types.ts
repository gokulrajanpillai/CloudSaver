// Re-export the inferred store state type for test helpers
import type { useStore } from '@/store'
export type AppStore = Parameters<Parameters<typeof useStore.setState>[0] extends (...args: unknown[]) => unknown ? never : typeof useStore.setState>[0]
