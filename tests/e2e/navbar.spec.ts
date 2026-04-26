import { expect, test } from './playwright';

import { setupUiParityApiMocks } from './ui_parity_mocks';

const primaryRoutes = [
  ['Overview', '/', 'Overview Dashboard'],
  ['Trends', '/trends', 'Trend & Keyword Insights'],
  ['Seasonal Events', '/seasonal-events', 'Seasonal Events Calendar'],
  ['Niches', '/niches', 'Niche Suggestions'],
  ['Listing Composer', '/listing-composer', 'Automated Listing Composer'],
  ['Search & Suggestions', '/search', 'Search & Suggestions'],
  ['A/B Tests', '/ab-tests', 'A/B Testing Lab'],
  ['Notifications & Scheduler', '/notifications', 'Notifications & Scheduler'],
  ['Settings', '/settings', 'Settings & Localization'],
] as const;

test.beforeEach(async ({ page }) => {
  await setupUiParityApiMocks(page);
});

test('control center shell exposes redesigned primary routes and quota', async ({ page }) => {
  await page.goto('/');

  for (const [label, href] of primaryRoutes) {
    const link = page.getByRole('link', { name: label });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('href', href);
  }

  await expect(page.getByTestId('quota')).toBeVisible();
  await expect(page.getByLabel('Store')).toBeVisible();
  await expect(page.getByLabel('Marketplace')).toBeVisible();
  await expect(page.getByLabel('Country')).toBeVisible();
  await expect(page.getByLabel('Language')).toBeVisible();
});

for (const [label, href, heading] of primaryRoutes) {
  test(`navigates to ${label}`, async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: label }).click();
    await expect(page).toHaveURL(new RegExp(`${escapeRegex(href === '/' ? '/' : href)}(?:\\?.*)?$`));
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
  });
}

test('global search deep links into the redesigned search page', async ({ page }) => {
  await page.goto('/');

  await page.getByPlaceholder('Search keywords, niches, products...').fill('teacher mug');
  await page.keyboard.press('Enter');

  await expect(page).toHaveURL(/\/search\?q=teacher\+mug/);
  await expect(page.getByRole('heading', { name: 'Search & Suggestions' })).toBeVisible();
  await expect(page.getByLabel('Keyword')).toHaveValue('teacher mug');
});

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
