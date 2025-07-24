import { test, expect } from '@playwright/test';

test('load review page and render list', async ({ page }) => {
  await page.goto('/images/review');
  await expect(page.getByTestId('image-list')).toBeVisible();
});
