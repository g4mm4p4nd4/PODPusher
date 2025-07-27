import { test, expect } from '@playwright/test';

test('notifications page lists items', async ({ page }) => {
  await page.route('**/api/notifications', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ id: 1, message: 'hello', read: false, created_at: '' }]),
    });
  });

  await page.route('**/api/notifications/1/read', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 1, message: 'hello', read: true, created_at: '' }),
    });
  });

  await page.goto('/notifications');
  await expect(page.getByText('Notifications')).toBeVisible();
  await expect(page.getByText('hello')).toBeVisible();
  await page.getByTestId('read-1').click();
});
