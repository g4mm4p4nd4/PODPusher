import { test, expect } from '@playwright/test';

// Simulated UI test for bulk product upload
// Uses a file input and verifies the filename is registered

test('bulk upload accepts CSV file', async ({ page }) => {
  await page.setContent('<input type="file" id="bulk" />');
  const fileInput = page.locator('#bulk');
  await fileInput.setInputFiles({
    name: 'products.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('name\nitem'),
  });
  await expect(fileInput).toHaveValue(/products.csv/);
});
