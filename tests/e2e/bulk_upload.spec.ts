import { test, expect } from '@playwright/test';

test('bulk uploader page renders', async ({ page }) => {
  await page.goto('/bulk');
  await expect(page.getByText('Bulk Uploader')).toBeVisible();
});
