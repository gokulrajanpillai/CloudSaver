import { render } from '@testing-library/react'
import type { RenderOptions } from '@testing-library/react'
import React from 'react'
import { useStore } from '@/store'
import type { AppStore } from './types'

export type PartialStoreState = Partial<AppStore>

/** Render a component with pre-seeded Zustand store state. */
export function renderWithStore(
  ui: React.ReactElement,
  state: PartialStoreState = {},
  options?: Omit<RenderOptions, 'wrapper'>,
) {
  useStore.setState(state)
  return render(ui, options)
}
