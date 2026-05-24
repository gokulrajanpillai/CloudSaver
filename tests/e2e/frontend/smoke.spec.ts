import { expect, test } from '@playwright/test'

test.describe('App loads', () => {
  test('renders without JS errors', async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', (err) => errors.push(err.message))

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    expect(errors.filter((e) => !e.includes('favicon'))).toHaveLength(0)
  })

  test('shows the Overview view by default', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible()
  })

  test('renders the navigation rail with all items', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    for (const label of ['Overview', 'Sources', 'Dupes', 'Map', 'Cleanup', 'Settings']) {
      await expect(page.getByRole('button', { name: label })).toBeVisible()
    }
  })

  test('shows the onboarding hero when no sources are connected', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText(/scan your first source/i)).toBeVisible()
  })
})
