import { test, expect } from '@playwright/test';

test('home page navbar shows links and quota', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('link', { name: 'Home' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Generate' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Categories' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Design Ideas' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Images' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Suggestions' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Analytics' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Notifications' })).toBeVisible();
  await expect(page.getByTestId('quota')).toHaveCount(1);
});
