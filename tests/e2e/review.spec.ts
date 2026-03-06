import { test, expect } from '@playwright/test';

const product = {
  id: 1,
  name: 'Test',
  image_url: '/test.png',
  rating: null,
  tags: [],
  flagged: false,
};

test('review page loads and allows rating', async ({ page }) => {
  const updates: Array<Record<string, unknown>> = [];

  await page.route('**/api/products/review**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([product]),
    });
  });

  await page.route('**/api/products/review/*', async (route) => {
    updates.push(route.request().postDataJSON() as Record<string, unknown>);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ...product, rating: 5, tags: ['foo'] }),
    });
  });

  await page.goto('/images/review');
  await expect(page.getByText('Image Review')).toBeVisible();

  await page.getByTestId('star-1-5').click();
  await expect.poll(() => updates.some((payload) => payload.rating === 5)).toBeTruthy();

  const tagInput = page.getByLabel('Add tag input');
  await tagInput.fill('foo');
  await page.getByRole('button', { name: 'Add' }).click();
  await expect.poll(() => updates.some((payload) => Array.isArray(payload.tags) && payload.tags.includes('foo'))).toBeTruthy();
});
