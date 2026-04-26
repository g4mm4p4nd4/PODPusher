import { mkdir } from 'node:fs/promises';
import path from 'node:path';

import { setupUiParityApiMocks } from '../../../tests/e2e/ui_parity_mocks';
import { expect, test } from '../../../tests/e2e/playwright';

const routes = [
  { path: '/', slug: 'overview', heading: 'Overview Dashboard' },
  { path: '/trends', slug: 'trends', heading: 'Trend & Keyword Insights' },
  { path: '/seasonal-events', slug: 'seasonal-events', heading: 'Seasonal Events Calendar' },
  { path: '/niches', slug: 'niches', heading: 'Niche Suggestions' },
  { path: '/search', slug: 'search', heading: 'Search & Suggestions' },
  { path: '/listing-composer', slug: 'listing-composer', heading: 'Automated Listing Composer' },
  { path: '/ab-tests', slug: 'ab-tests', heading: 'A/B Testing Lab' },
  { path: '/notifications', slug: 'notifications', heading: 'Notifications & Scheduler' },
  { path: '/settings', slug: 'settings', heading: 'Settings & Localization' },
] as const;

test.use({ viewport: { width: 1448, height: 1086 }, deviceScaleFactor: 1 });

test.beforeEach(async ({ page }) => {
  await setupUiParityApiMocks(page);
});

for (const route of routes) {
  test(`capture ${route.path}`, async ({ page }) => {
    await page.goto(route.path);
    await expect(page.getByRole('heading', { name: route.heading })).toBeVisible();

    const outputDir = path.join(process.cwd(), 'output', 'playwright', 'ui-parity');
    await mkdir(outputDir, { recursive: true });
    await page.screenshot({
      path: path.join(outputDir, `${route.slug}.png`),
      fullPage: false,
      animations: 'disabled',
    });
  });
}
