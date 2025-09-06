import { test, expect } from '@playwright/test';

const csv = 'title,description,price,category,variants,image_urls\nTee,desc,9.99,apparel,"[]","[]"\n';

test('bulk uploader shows results', async ({ page }) => {
  await page.route('**/api/bulk_create', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        created: [{ index: 0, product: { title: 'Shirt' } }],
        errors: [],
      }),
    });
  });

  await page.goto('/bulk-upload');
  await page.setInputFiles('input[type="file"]', {
    name: 'products.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from(csv),
  });
  await expect(page.getByText('Shirt')).toBeVisible();
});
