import { test, expect } from '@playwright/test';

test('quota indicator displays usage', async ({ page }) => {
  await page.route('**/user/plan', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ plan: 'free', images_used: 0, limit: 20 }),
    });
  });
  await page.goto('http://localhost:3000');
  await expect(page.getByTestId('quota')).toHaveText('0/20 images');
});
