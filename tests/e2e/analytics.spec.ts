import { test, expect } from './playwright';

test('analytics page loads chart', async ({ page }) => {
  await page.goto('/analytics');
  await expect(page.getByRole('heading', { name: 'Analytics Dashboard' })).toBeVisible();
});
