const { test, expect } = require("@playwright/test");

test("theme controls switch and persist explicit preferences", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator("html")).toHaveAttribute("data-theme-preference", "system");
  await expect(page.getByRole("button", { name: "System" })).toHaveAttribute("aria-pressed", "true");

  await page.getByRole("button", { name: "Dark" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme-preference", "dark");
  await expect(page.getByRole("button", { name: "Dark" })).toHaveAttribute("aria-pressed", "true");

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme-preference", "dark");

  await page.getByRole("button", { name: "Light" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.locator("html")).toHaveAttribute("data-theme-preference", "light");

  await page.getByRole("button", { name: "System" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme-preference", "system");
});

test("workspace navigation still works after theme changes", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Dark" }).click();
  await page.getByRole("button", { name: "Files" }).click();

  await expect(page.locator('[data-view="files"]')).toHaveClass(/active/);
  await expect(page.getByRole("heading", { name: "Files" })).toBeVisible();
});
