import { test, expect } from '@playwright/test';

test('ab test page creates test', async ({ page }) => {
  await page.route('**/ab_tests', route => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 1 }),
      });
    } else {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { variant_name: 'A', impressions: 0, clicks: 0, conversion_rate: 0 },
          { variant_name: 'B', impressions: 0, clicks: 0, conversion_rate: 0 },
        ]),
      });
    }
  });

  await page.goto('/ab-tests');
  await page.getByPlaceholder('Title').fill('My Test');
  await page.getByPlaceholder('Variant A').fill('A');
  await page.getByPlaceholder('Variant B').fill('B');
  await page.getByRole('button', { name: 'Create Test' }).click();
  await expect(page.getByText('Test ID:')).toBeVisible();
});
