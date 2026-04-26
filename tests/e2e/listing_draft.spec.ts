import { expect, test } from './playwright';

import { setupUiParityApiMocks } from './ui_parity_mocks';

test.beforeEach(async ({ page }) => {
  await setupUiParityApiMocks(page);
});

test('listing composer saves draft id in local storage', async ({ page }) => {
  await page.goto('/listing-composer');

  await page.getByLabel('Title').fill('Draft Title');
  await page.getByLabel('Description').fill('Draft description');
  await page.getByRole('button', { name: 'Save Draft' }).click();

  await expect(page.getByText('Draft saved just now')).toBeVisible();
  await expect.poll(() => page.evaluate(() => window.localStorage.getItem('draftId'))).toBe('101');
});

test('listing composer consumes direct handoff query params', async ({ page }) => {
  await page.goto('/listing-composer?source=e2e&niche=Dog%20Mom%20Gifts&keyword=dog%20mom&product_type=Mug&audience=Dog%20Lovers&tags=dog%20mom,coffee');

  await expect(page.getByLabel('Niche')).toHaveValue('Dog Mom Gifts');
  await expect(page.getByLabel('Primary Keyword')).toHaveValue('dog mom');
  await expect(page.getByLabel('Product Type')).toHaveValue('Mug');
  await expect(page.getByLabel('Target Audience')).toHaveValue('Dog Lovers');
  await expect(page.getByText('Prefilled from e2e')).toBeVisible();
  await expect(page.getByText('coffee')).toBeVisible();
});
