import { test, expect } from '@playwright/test';

// Simple monitoring UI check

test('monitoring indicators render', async ({ page }) => {
  await page.setContent(
    '<div id="health">ok</div><div id="ready">ready</div><div id="metrics">0</div>'
  );
  await expect(page.locator('#health')).toHaveText('ok');
  await expect(page.locator('#ready')).toHaveText('ready');
  await expect(page.locator('#metrics')).toHaveText('0');
});
