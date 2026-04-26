import { expect, test } from './playwright';

import { setupUiParityApiMocks } from './ui_parity_mocks';

test.beforeEach(async ({ page }) => {
  await setupUiParityApiMocks(page);
});

test('notifications dashboard marks feed items as read', async ({ page }) => {
  await page.goto('/notifications');

  await expect(page.getByRole('heading', { name: 'Notifications & Scheduler' })).toBeVisible();
  await expect(page.getByText('A/B test Dog Mom Tee v2 is winning.')).toBeVisible();
  await page.getByTestId('read-42').click();

  await expect(page.getByTestId('read-42')).toHaveCount(0);
});

test('notifications dashboard schedules a digest job', async ({ page }) => {
  await page.goto('/notifications');

  await page.getByRole('button', { name: 'Manage Schedules' }).click();
  await page.getByLabel('Schedule name').fill('Seasonal Event Sync');
  await page.getByLabel('Frequency').selectOption('Daily');
  await page.getByRole('button', { name: 'Save' }).click();

  await expect(page.getByText('Schedule saved and queued for the next run.')).toBeVisible();
});

test('notifications dashboard saves alert rules and keeps Slack non-blocking', async ({ page }) => {
  await page.goto('/notifications');

  await page.getByLabel('Rule name').fill('Low Quota Regression Guard');
  await page.getByRole('button', { name: 'New Rule' }).click();
  await expect(page.getByText('Alert rule saved.')).toBeVisible();

  const slackCard = page.locator('section').filter({ hasText: 'Slack Integration' });
  await expect(slackCard.getByText('Credential-backed setup is unavailable in local mode.')).toBeVisible();
  await slackCard.getByRole('button', { name: 'Needs setup' }).click();
  await expect(page.getByRole('status')).toContainText('Slack is unavailable in local mode');
});
