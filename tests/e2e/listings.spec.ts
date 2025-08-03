import { test, expect } from '@playwright/test';

test('listing composer suggests tags', async ({ page }) => {
  await page.route('**/api/ideation/suggest-tags', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(['funny', 'dog'])
    });
  });
  await page.goto('/listings');
  await page.getByLabel('Title').fill('Funny Dog Shirt');
  await page.getByLabel('Description').fill('A hilarious t-shirt');
  await page.getByRole('button', { name: 'Suggest Tags' }).click();
  await expect(page.getByRole('button', { name: 'funny' })).toBeVisible();
  await page.getByRole('button', { name: 'funny' }).click();
  await expect(page.getByText('Tags (1/13)')).toBeVisible();
});
