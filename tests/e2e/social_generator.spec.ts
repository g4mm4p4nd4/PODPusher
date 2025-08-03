import { test, expect } from '@playwright/test';

test('social generator creates caption', async ({ page }) => {
  await page.route('**/social/post', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ caption: 'hello', image_url: 'http://example.com/img.png' })
    });
  });
  await page.goto('/social-generator');
  await page.getByLabel('prompt').fill('idea');
  await page.getByRole('button', { name: 'Generate' }).click();
  await expect(page.getByText('hello')).toBeVisible();
});
