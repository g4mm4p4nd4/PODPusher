import { test, expect } from '@playwright/test';

test('images tab allows generation', async ({ page }) => {
  await page.route('**/api/images/generate', route => {
    route.fulfill({ status: 200, body: JSON.stringify({ urls: ['http://example.com/img.png'] }) });
  });
  await page.goto('/');
  await page.click('text=Images');
  await page.fill('input[name="ideaId"]', '1');
  await page.fill('input[name="style"]', 'modern');
  await page.click('button:has-text("Generate")');
  await expect(page.locator('img')).toHaveCount(1);
});
