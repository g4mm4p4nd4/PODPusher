import { expect, test } from './playwright';

import { setupUiParityApiMocks } from './ui_parity_mocks';

test.beforeEach(async ({ page }) => {
  await setupUiParityApiMocks(page);
});

test('A/B testing lab creates a product experiment from the redesigned form', async ({ page }) => {
  await page.goto('/ab-tests');

  await expect(page.getByRole('heading', { name: 'A/B Testing Lab' })).toBeVisible();
  await page.getByPlaceholder('Retro Sunset Tee - Title Test').fill('Dog Mom Title Test');
  await page.getByLabel('Select Product').selectOption('102');
  await page.getByRole('button', { name: 'Title' }).click();
  await page.getByPlaceholder('Control').fill('Title A');
  await page.getByPlaceholder('Challenger').fill('Title B');
  await page.getByLabel('Traffic Split').selectOption('60/40');
  await page.locator('#create-ab-test').getByRole('button', { name: 'Create A/B Test' }).click();

  await expect(page.getByRole('status')).toContainText('Created A/B test in local experiment state.');
  await expect(page.getByRole('cell', { name: /Dog Mom Title Test/ })).toBeVisible();
  await expect(page.getByText('Title A').first()).toBeVisible();
  await expect(page.getByText('Title B').first()).toBeVisible();
});

test('A/B testing lab pushes the selected winner to listing state', async ({ page }) => {
  await page.goto('/ab-tests');

  await expect(page.getByRole('cell', { name: /Retro Sunset Tee - Thumbnail Test/ })).toBeVisible();
  await expect(page.getByText('Thumbnail B').first()).toBeVisible();
  await page.getByRole('button', { name: 'Push Winner to Listing' }).click();

  await expect(page.getByRole('status')).toContainText('Winner pushed into listing draft state.');
  await expect(page.getByRole('cell', { name: /Retro Sunset Tee - Thumbnail Test/ })).toContainText('#7');
});
