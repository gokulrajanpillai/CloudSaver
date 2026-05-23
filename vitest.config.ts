import path from 'path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    setupFiles: ['src/__tests__/setup.ts'],
    globals: true,
    coverage: {
      provider: 'v8',
      include: ['src/**'],
      exclude: ['src/__tests__/**', 'src/components/ui/**'],
      thresholds: { lines: 70, branches: 65 },
    },
  },
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
})
