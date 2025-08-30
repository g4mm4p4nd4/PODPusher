import { test, expect } from '@playwright/test';

const csv = `title,description,base_product_type,variants\nT1,Desc,shirt,v1`;

test('upload csv shows progress', async ({ page }) => {
  await page.route('**/api/bulk_create', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ created: [1], errors: [] })
    });
  });
  await page.goto('/bulk-create');
  await page.setInputFiles('input[type="file"]', {
    name: 'data.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from(csv)
  });
  await expect(page.getByText('Upload Progress')).toBeVisible();
  await expect(page.getByText('1 created')).toBeVisible();
});
