const { defineConfig } = require('@playwright/test')

module.exports = defineConfig({
  testDir: 'tests/e2e/frontend',
  timeout: 30000,
  use: {
    baseURL: 'http://127.0.0.1:1420',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      // Python backend — provides /api/* routes
      command: 'python3 -m cloudsaver.web_server --host 127.0.0.1 --port 8765',
      url: 'http://127.0.0.1:8765/api/health',
      reuseExistingServer: true,
      timeout: 15000,
    },
    {
      // Vite dev server — serves the React SPA
      command: 'npm run dev',
      url: 'http://127.0.0.1:1420',
      reuseExistingServer: true,
      timeout: 30000,
    },
  ],
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
})
