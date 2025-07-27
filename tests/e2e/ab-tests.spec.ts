import { test, expect } from '@playwright/test';

test('AB test creation flow', async ({ page }) => {
  await page.route('**/api/ab_tests', async route => {
    if (route.request().method() === 'POST') {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1 }) });
    }
  });
  await page.route('**/api/ab_tests/1', async route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 1, variants: [] }) });
  });

  await page.goto('/ab-tests');
  await page.fill('input[aria-label="Title A"]', 'A');
  await page.fill('input[aria-label="Title B"]', 'B');
  await page.click('text=Create Test');
  await expect(page.getByText('Test ID: 1')).toBeVisible();
});
