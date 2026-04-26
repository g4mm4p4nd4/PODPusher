import { expect, test } from './playwright';

import { setupUiParityApiMocks } from './ui_parity_mocks';

test.beforeEach(async ({ page }) => {
  await setupUiParityApiMocks(page);
});

test('search page filters products and saves the current search', async ({ page }) => {
  await page.goto('/search');

  await expect(page.getByRole('heading', { name: 'Search & Suggestions' })).toBeVisible();
  const searchForm = page.locator('main form').first();
  await searchForm.getByLabel('Keyword').fill('dog mom');
  await searchForm.getByLabel('Category').selectOption('Apparel');
  await searchForm.getByLabel('Marketplace').selectOption('etsy');
  await searchForm.getByRole('button', { name: 'Search', exact: true }).click();

  await expect(page.getByRole('cell', { name: 'Retro Dog Mom T-Shirt', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Save Search' }).click();
  await expect(page.getByText('Search saved')).toBeVisible();
});

test('search result actions add watchlist items and generated tags', async ({ page }) => {
  await page.goto('/search');

  const row = page.getByRole('row').filter({ hasText: 'Retro Dog Mom T-Shirt' });
  await expect(row).toBeVisible();

  await row.getByRole('button', { name: 'Watch' }).click();
  await expect(page.getByText('Added Retro Dog Mom T-Shirt to watchlist')).toBeVisible();

  await row.getByRole('button', { name: 'Tags' }).click();
  await expect(page.getByText('Generated 3 tags')).toBeVisible();
  await expect(page.getByLabel('Generated Tags')).toContainText('retro beach');
});

test('search sends selected product and tags to listing composer', async ({ page }) => {
  await page.goto('/search');

  const row = page.getByRole('row').filter({ hasText: 'Retro Dog Mom T-Shirt' });
  await row.getByRole('button', { name: 'Tags' }).click();
  await expect(page.getByText('Generated 3 tags')).toBeVisible();
  await row.getByRole('link', { name: 'Compose' }).click();

  await expect(page).toHaveURL(/\/listing-composer\?.*source=search/);
  await expect(page.getByRole('heading', { name: 'Automated Listing Composer' })).toBeVisible();
  await expect(page.getByLabel('Primary Keyword')).toHaveValue('dog mom summer vibes');
  await expect(page.getByLabel('Product Type')).toHaveValue('Apparel');
  await expect(page.getByText('retro beach').first()).toBeVisible();
});
