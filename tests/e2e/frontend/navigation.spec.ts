import { expect, test } from '@playwright/test'

const views = [
  { nav: 'Sources', heading: 'Sources' },
  { nav: 'Dupes', heading: 'Cross-Source Duplicates' },
  { nav: 'Cleanup', heading: 'Quarantine' },
  { nav: 'Settings', heading: 'Settings' },
  { nav: 'Overview', heading: 'Overview' },
] as const

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  for (const { nav, heading } of views) {
    test(`clicking "${nav}" in nav rail shows the ${heading} view`, async ({ page }) => {
      await page.getByRole('button', { name: nav }).click()
      await expect(page.getByRole('heading', { name: heading }).first()).toBeVisible()
    })
  }

  test('Overview is the default view on first load', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible()
  })
})
