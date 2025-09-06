import { test, expect } from '@playwright/test';

test('social generator creates caption', async ({ page }) => {
  await page.route('**/api/social/generate', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ caption: 'hello', image: null })
    });
  });
  await page.goto('/social-generator');
  await page.getByPlaceholder('Product title').fill('idea');
  await page.getByPlaceholder('Product type').fill('tshirt');
  await page.getByRole('button', { name: 'Generate' }).click();
  await expect(page.getByDisplayValue('hello')).toBeVisible();
});

test('social generator form fields visible', async ({ page }) => {
  await page.goto('/social-generator');
  await expect(page.getByPlaceholder('Product title')).toBeVisible();
  await expect(page.getByPlaceholder('Product type')).toBeVisible();
});
