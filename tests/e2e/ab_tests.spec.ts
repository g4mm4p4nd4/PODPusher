import { test, expect } from '@playwright/test';

test('ab tests page creates experiment', async ({ page }) => {
  await page.route('**/ab_tests', route => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          name: 'Test',
          experiment_type: 'image',
          start_time: null,
          end_time: null,
          variants: [{ id: 10, test_id: 1, name: 'A', weight: 1 }],
        }),
      });
    } else {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 10,
            test_id: 1,
            name: 'A',
            weight: 1,
            impressions: 1,
            clicks: 1,
            conversion_rate: 1,
            experiment_type: 'image',
            start_time: null,
            end_time: null,
          },
        ]),
      });
    }
  });

  await page.goto('/ab_tests');
  await page.getByPlaceholder('Test Name').fill('MyTest');
  await page
    .getByPlaceholder('Variants (comma separated)')
    .fill('A');
  await page
    .getByPlaceholder('Traffic Weights (comma separated)')
    .fill('1');
  await page.getByRole('button', { name: 'Create' }).click();
  await expect(page.getByTestId('imp-10')).toBeVisible();
});
