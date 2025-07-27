import { test, expect } from '@playwright/test';

test('listing composer counts and suggests tags', async ({ page }) => {
  await page.route('**/suggest-tags', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(['foo', 'bar']),
    });
  });

  await page.goto('/listings');
  await expect(page.getByText('Listing Composer')).toBeVisible();
  const title = page.getByTestId('title-input');
  await title.fill('Hello');
  await expect(page.getByText('5/140')).toBeVisible();
  await page.getByTestId('suggest-button').click();
  await expect(page.getByTestId('tags-input')).toHaveValue('foo, bar');
});
