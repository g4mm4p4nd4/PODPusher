import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { expect, test, type Page } from './playwright';

import { setupUiParityApiMocks } from './ui_parity_mocks';

const routeContracts = [
  {
    path: '/',
    heading: 'Overview Dashboard',
    content: ['Keyword Growth Trend', 'Top Rising Niches', 'Recent Listing Composer'],
  },
  {
    path: '/trends',
    heading: 'Trend & Keyword Insights',
    content: ['Trending Keywords', 'Related Design Ideas', 'Suggested Tag Clusters'],
  },
  {
    path: '/seasonal-events',
    heading: 'Seasonal Events Calendar',
    content: ['Upcoming High-Priority Events', 'Recommended Keywords', 'Create Early, Sell Early'],
  },
  {
    path: '/niches',
    heading: 'Niche Suggestions',
    content: ['Suggested Niches', 'Why this niche?', 'Localized Variants'],
  },
  {
    path: '/search',
    heading: 'Search & Suggestions',
    content: ['Search Results', 'Suggestions & Inspiration', 'Top Result Comparison'],
  },
  {
    path: '/listing-composer',
    heading: 'Automated Listing Composer',
    content: ['Product Inputs', 'Generated Title', 'Marketplace Compliance'],
  },
  {
    path: '/ab-tests',
    heading: 'A/B Testing Lab',
    content: ['Experiments', 'Create New Test', 'Push Winner to Listing'],
  },
  {
    path: '/notifications',
    heading: 'Notifications & Scheduler',
    content: ['Digest Schedule', 'Rule Builder', 'Notification Preferences'],
  },
  {
    path: '/settings',
    heading: 'Settings & Localization',
    content: ['Localization Settings', 'Regional Niche Preferences', 'Users & Roles'],
  },
] as const;

test.beforeEach(async ({ page }) => {
  await setupUiParityApiMocks(page);
});

for (const route of routeContracts) {
  test(`${route.path} renders redesigned UI contract`, async ({ page }) => {
    await page.goto(route.path);

    await expect(page.getByRole('heading', { name: route.heading })).toBeVisible();
    for (const text of route.content) {
      await expect(page.getByText(text, { exact: false }).first()).toBeVisible();
    }

    await maybeCaptureRoute(page, route.path);
  });
}

async function maybeCaptureRoute(page: Page, routePath: string) {
  if (process.env.UI_PARITY_CAPTURE_SCREENSHOTS !== '1') return;

  const outputDir = path.join(process.cwd(), 'output', 'playwright', 'ui-parity');
  await mkdir(outputDir, { recursive: true });
  const slug = routePath === '/' ? 'overview' : routePath.replace(/^\//, '').replace(/\//g, '-');
  await page.screenshot({ path: path.join(outputDir, `${slug}.png`), fullPage: true });
}
