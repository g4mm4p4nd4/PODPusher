import { test, expect } from '@playwright/test';

test('ab tests page creates experiment', async ({ page }) => {
  await page.route('**/ab_tests', route => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 1, name: 'Test', variants: [{ id: 10, name: 'A' }] }),
      });
    } else {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 10, test_id: 1, name: 'A', impressions: 1, clicks: 1, conversion_rate: 1 }]),
      });
    }
  });

  await page.goto('/ab_tests');
  await page.getByPlaceholder('Test Name').fill('MyTest');
  await page.getByPlaceholder('Variants (comma separated)').fill('A');
  await page.getByRole('button', { name: 'Create' }).click();
  await expect(page.getByTestId('imp-10')).toBeVisible();
});
