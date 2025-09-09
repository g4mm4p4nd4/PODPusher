import { test, expect } from '@playwright/test';

test('images page generates and shows images', async ({ page }) => {
  await page.route('**/api/images/generate', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ id: 1, url: '/img.png' }]),
    });
  });

  await page.goto('/images');
  await page.fill('input[placeholder="Idea ID"]', '1');
  await page.fill('input[placeholder="Style"]', 'cartoon');
  await page.getByRole('button', { name: 'Generate' }).click();
  await expect(page.locator('img')).toHaveCount(1);
});
