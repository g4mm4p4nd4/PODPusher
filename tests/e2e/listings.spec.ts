import { expect, test } from './playwright';

import { setupUiParityApiMocks } from './ui_parity_mocks';

test.beforeEach(async ({ page }) => {
  await setupUiParityApiMocks(page);
});

test('listing composer suggests and applies generated tags', async ({ page }) => {
  await page.goto('/listing-composer');

  await expect(page.getByRole('heading', { name: 'Automated Listing Composer' })).toBeVisible();
  await page.getByLabel('Title').fill('Funny Dog Mom Shirt');
  await page.getByLabel('Description').fill('A hilarious t-shirt for dog moms.');
  await page.getByRole('button', { name: 'Suggest Tags' }).click();

  await expect(page.getByRole('button', { name: 'dog mom' })).toBeVisible();
  await page.getByRole('button', { name: 'dog mom' }).click();
  await expect(page.getByText('Tags (1/13)')).toBeVisible();
});

test('listing composer queues and exports a draft without live marketplace credentials', async ({ page }) => {
  await page.goto('/listing-composer');

  await page.getByLabel('Title').fill('Retro Dog Mom T-Shirt');
  await page.getByLabel('Description').fill('A trend-aware shirt for dog moms.');
  await page.getByRole('button', { name: 'Save Draft' }).click();
  await expect(page.getByText('Draft saved just now')).toBeVisible();

  await page.getByRole('button', { name: 'Publish Queue' }).click();
  await expect(page.getByText(/Queue queued: draft/)).toBeVisible();

  await page.getByRole('button', { name: 'Export' }).click();
  await expect(page.getByText(/Export ready: draft/)).toBeVisible();
});
