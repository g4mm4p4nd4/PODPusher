import { test, expect } from '@playwright/test';

test('ab tests page creates experiment', async ({ page }) => {
  await page.route('**/ab_tests', async (route) => {
    if (!route.request().url().startsWith('http://localhost:8000/')) {
      await route.continue();
      return;
    }

    if (route.request().method() === 'POST') {
      await route.fulfill({
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
      return;
    }

    await route.continue();
  });

  await page.route('**/ab_tests/*/metrics', async (route) => {
    if (!route.request().url().startsWith('http://localhost:8000/')) {
      await route.continue();
      return;
    }

    await route.fulfill({
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
  });

  await page.goto('/ab_tests');
  await page.getByPlaceholder('Test Name').fill('MyTest');
  await page.getByPlaceholder('Variants (comma separated)').fill('A');
  await page.getByPlaceholder('Traffic Weights (comma separated)').fill('1');
  await page.getByRole('button', { name: 'Create' }).click();
  await expect(page.getByTestId('imp-10')).toBeVisible();
});
