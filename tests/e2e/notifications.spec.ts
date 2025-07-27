import { test, expect } from '@playwright/test';

test('quota reset notification shows', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('notifications')).toBeVisible();
});
