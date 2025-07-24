import { test, expect } from '@playwright/test';

test('analytics page loads chart', async ({ page }) => {
  await page.goto('/analytics');
  await expect(page.getByText('Keyword Analytics')).toBeVisible();
});
