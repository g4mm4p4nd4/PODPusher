import { test, expect } from '@playwright/test';

test('ab tests page creates experiment', async ({ page }) => {
  await page.route('**/api/ab-tests/**', route => {
    const url = route.request().url;
    const method = route.request().method();
    if (method === 'POST' && url.endsWith('/click')) {
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    } else if (method === 'POST' && url.endsWith('/impression')) {
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    } else if (method === 'POST') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          name: 'Test',
          variants: [
            {
              id: 10,
              listing_id: 123,
              title: 'A',
              description: 'Desc',
            },
          ],
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
            listing_id: 123,
            title: 'A',
            description: 'Desc',
            impressions: 1,
            clicks: 1,
            conversion_rate: 1,
          },
        ]),
      });
    }
  });

  await page.goto('/ab-tests');
  await page.getByLabel('Test Name').fill('MyTest');
  await page.getByLabel('Listing ID').fill('123');
  await page.getByLabel('Variant Title').fill('A');
  await page.getByLabel('Variant Description').fill('Desc');
  await page.getByRole('button', { name: 'Create' }).click();
  const clickResp = await page.request.post('/api/ab-tests/10/click');
  expect(clickResp.ok()).toBeTruthy();
  await expect(page.getByTestId('imp-10')).toBeVisible();
});
