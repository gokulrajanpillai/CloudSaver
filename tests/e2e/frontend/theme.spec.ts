import { expect, test } from '@playwright/test'

test.describe('Theme', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    // Navigate to Settings
    await page.getByRole('button', { name: 'Settings' }).click()
  })

  test('default theme is "system"', async ({ page }) => {
    const select = page.getByRole('combobox')
    await expect(select).toHaveValue('system')
  })

  test('selecting "dark" persists after page reload', async ({ page }) => {
    await page.getByRole('combobox').selectOption('dark')
    await page.reload()
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: 'Settings' }).click()
    await expect(page.getByRole('combobox')).toHaveValue('dark')
  })

  test('selecting "light" persists after reload', async ({ page }) => {
    await page.getByRole('combobox').selectOption('light')
    await page.reload()
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: 'Settings' }).click()
    await expect(page.getByRole('combobox')).toHaveValue('light')
  })
})
