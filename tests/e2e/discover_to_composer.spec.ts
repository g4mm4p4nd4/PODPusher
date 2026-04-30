import { expect, test } from './playwright';

import { setupUiParityApiMocks } from './ui_parity_mocks';

test.beforeEach(async ({ page }) => {
  await setupUiParityApiMocks(page);
});

test('trend discovery hands keyword context to the listing composer', async ({ page }) => {
  await page.goto('/trends');

  await expect(page.getByRole('heading', { name: 'Trend & Keyword Insights' })).toBeVisible();
  await page.getByRole('link', { name: 'Use in Composer' }).first().click();

  await expect(page).toHaveURL(/\/listing-composer\?.*source=trends/);
  await expect(page.getByRole('heading', { name: 'Automated Listing Composer' })).toBeVisible();
  await expect(page.getByLabel('Niche', { exact: true })).toHaveValue('dog mom');
  await expect(page.getByLabel('Primary Keyword')).toHaveValue('dog mom');
  await expect(page.getByLabel('Product Type')).toHaveValue('T-Shirt');
  await expect(page.getByText('Dog Mom Shirt Bestseller')).toBeVisible();
  await expect(page.getByText(/Market signal attached from amazon/)).toBeVisible();
  await expect(page.getByText('Prefilled from trends')).toBeVisible();
});

test('seasonal event discovery hands occasion context to composer', async ({ page }) => {
  await page.goto('/seasonal-events');

  await expect(page.getByRole('heading', { name: 'Seasonal Events Calendar' })).toBeVisible();
  await page.getByRole('link', { name: 'Use in Composer' }).click();

  await expect(page).toHaveURL(/\/listing-composer\?.*source=seasonal/);
  await expect(page.getByLabel('Occasion')).toHaveValue('Back to School');
  await expect(page.getByLabel('Primary Keyword')).toHaveValue('back to school');
});

test('niche suggestion links into composer and A/B setup routes', async ({ page }) => {
  await page.goto('/niches');

  await expect(page.getByRole('heading', { name: 'Niche Suggestions' })).toBeVisible();
  await page.getByRole('link', { name: 'Create Listing' }).click();

  await expect(page).toHaveURL(/\/listing-composer\?.*source=niches/);
  await expect(page.getByRole('heading', { name: 'Automated Listing Composer' })).toBeVisible();

  await page.goto('/niches');
  const startABTest = page.getByRole('link', { name: 'Start A/B Test' });
  await startABTest.scrollIntoViewIfNeeded();
  await startABTest.click();
  await expect(page).toHaveURL(/\/ab-tests\?.*source=niche/);
  await expect(page.getByRole('heading', { name: 'A/B Testing Lab' })).toBeVisible();
});
