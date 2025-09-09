import { test, expect } from '@playwright/test';
import path from 'path';

const file = path.join(__dirname, 'fixtures', 'mock_trend.html');

test('mock trend page selectors', async ({ page }) => {
  await page.goto('file://' + file);
  const items = await page.$$('div.item');
  expect(items.length).toBeGreaterThan(0);
  const title = await items[0].$('.title');
  await expect(title).not.toBeNull();
  expect(await title?.textContent()).toBe('Funny Cats');
  const likes = await items[0].$('.likes');
  expect(await likes?.textContent()).toBe('10');
});
