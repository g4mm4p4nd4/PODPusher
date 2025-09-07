import { test, expect } from '@playwright/test';

test('notifications page lists items', async ({ page }) => {
  await page.route('**/api/notifications', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ id: 1, message: 'hello', type: 'info', read: false, created_at: '', delivery_method: 'in_app', status: 'sent' }]),
    });
  });

  await page.route('**/api/notifications/mark_read', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 1, message: 'hello', type: 'info', read: true, created_at: '', delivery_method: 'in_app', status: 'sent' }),
    });
  });

  await page.goto('/notifications');
  await expect(page.getByText('Notifications')).toBeVisible();
  await expect(page.getByText('hello')).toBeVisible();
  await page.getByTestId('read-1').click();
});

test('schedule form submits', async ({ page }) => {
  await page.route('**/api/notifications/schedule', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });
  await page.goto('/schedule');
  await page.getByLabel('Message').fill('hi');
  await page.getByRole('button', { name: 'Schedule' }).click();
});
