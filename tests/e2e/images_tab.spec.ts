import { test, expect } from '@playwright/test';

const images = [
  { id: 1, url: '/img1.png' },
];

test('images tab loads and can regenerate', async ({ page }) => {
  await page.route('**/api/images*', route => {
    if (route.request().method() === 'GET') {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(images) });
    } else {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(['/img2.png']) });
    }
  });

  await page.goto('/images');
  await expect(page.getByText('Images')).toBeVisible();
  await page.getByText('Regenerate').click();
  await expect(page.getByText('Images')).toBeVisible();
});
