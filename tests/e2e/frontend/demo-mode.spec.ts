import { expect, test } from '@playwright/test'

test.describe('Demo mode', () => {
  async function loadDemo(page: import('@playwright/test').Page) {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: 'Settings' }).click()
    await page.getByRole('button', { name: /load demo data/i }).click()
  }

  test('loads demo sources and shows them in Sources view', async ({ page }) => {
    await loadDemo(page)
    await page.getByRole('button', { name: 'Sources' }).click()

    await expect(page.getByText('iCloud Drive')).toBeVisible()
    await expect(page.getByText('Downloads')).toBeVisible()
  })

  test('Overview shows metrics after demo load', async ({ page }) => {
    await loadDemo(page)
    await page.getByRole('button', { name: 'Overview' }).click()

    // Monthly cost should be non-zero
    const costText = await page.getByText(/\$\d+\.\d+/).textContent()
    expect(Number(costText?.replace('$', ''))).toBeGreaterThan(0)
  })

  test('Overview shows Recommended Next Steps plan cards', async ({ page }) => {
    await loadDemo(page)
    await page.getByRole('button', { name: 'Overview' }).click()

    await expect(page.getByText(/remove extra copies/i)).toBeVisible()
    await expect(page.getByText(/create reduced image copies/i)).toBeVisible()
  })

  test('Duplicates view shows cross-source groups', async ({ page }) => {
    await loadDemo(page)
    await page.getByRole('button', { name: 'Dupes' }).click()

    await expect(page.getByText('Cross-Source Duplicates')).toBeVisible()
    await expect(page.getByText(/high confidence/i)).toBeVisible()
  })

  test('Duplicates view shows visually similar image groups with thumbnails', async ({ page }) => {
    await loadDemo(page)
    await page.getByRole('button', { name: 'Dupes' }).click()

    await expect(page.getByText('Visually Similar Images')).toBeVisible()
    await expect(page.getByText(/97% similar/i)).toBeVisible()

    const imgs = page.locator('img[src*="/demo/"]')
    expect(await imgs.count()).toBeGreaterThanOrEqual(2)
  })

  test('clearing demo data reverts to onboarding hero', async ({ page }) => {
    await loadDemo(page)

    // Clear demo
    await page.getByRole('button', { name: /clear demo data/i }).click()
    await page.getByRole('button', { name: 'Overview' }).click()

    await expect(page.getByText(/scan your first source/i)).toBeVisible()
  })

  test('demo active notice appears in Settings after load', async ({ page }) => {
    await loadDemo(page)
    await expect(page.getByText(/demo data is active/i)).toBeVisible()
  })

  test('"Load demo data" button is disabled while demo is active', async ({ page }) => {
    await loadDemo(page)
    const loadBtn = page.getByRole('button', { name: /load demo data/i })
    await expect(loadBtn).toBeDisabled()
  })
})
