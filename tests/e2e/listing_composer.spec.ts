import { test, expect } from '@playwright/test';

test('listing composer tag suggestions', async ({ page }) => {
  await page.goto('/listing');
  await page.fill('textarea', 'cute cat mug');
  await page.click('[data-testid="suggest-btn"]');
  await expect(page.locator('[data-testid="tag-list"] li').first()).toBeVisible();
});
