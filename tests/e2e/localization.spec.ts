import { expect, test } from './playwright';

import { setupUiParityApiMocks } from './ui_parity_mocks';

test.beforeEach(async ({ page }) => {
  await setupUiParityApiMocks(page);
});

test('settings localization tab scopes editable content and saves changes', async ({ page }) => {
  await page.goto('/settings');

  await expect(page.getByRole('heading', { name: 'Settings & Localization' })).toBeVisible();
  await expect(page.getByText('Localization Settings')).toBeVisible();
  await expect(page.getByText('admin@podpusher.com')).toHaveCount(0);

  await page.getByLabel('Currency').selectOption('GBP');
  await page.getByLabel('Default Language').selectOption('fr');
  await page.getByLabel('Marketplace Regions').fill('US, GB, FR');
  await page.getByRole('button', { name: 'Save Changes' }).click();

  await expect(page.getByRole('status')).toContainText('Localization settings saved.');
  await expect(page.getByLabel('Currency')).toHaveValue('GBP');
});

test('settings tabs expose users, quotas, integrations, and non-blocking provider status', async ({ page }) => {
  await page.goto('/settings');

  await page.getByRole('button', { name: 'Users & Roles' }).click();
  await expect(page.getByText('admin@podpusher.com')).toBeVisible();

  await page.getByRole('button', { name: 'Quotas' }).click();
  await page.getByRole('button', { name: 'View Usage Details' }).click();
  await expect(page.getByText('Usage ledger is showing explicit demo data.')).toBeVisible();
  await expect(page.getByText('image_generation')).toBeVisible();

  await page.getByRole('button', { name: 'Integrations' }).click();
  await expect(page.getByText('Non-blocking fallback data is active.')).toBeVisible();
  await page.getByRole('button', { name: 'Configure' }).last().click();
  await expect(page.getByRole('status')).toContainText('Credential-backed setup is unavailable in local mode.');
});
