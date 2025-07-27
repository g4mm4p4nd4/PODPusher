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
  await page.route('**/api/images/review', route => {
    if (route.request().method() === 'GET') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([product]),
      });
    } else {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...product, rating: 5, tags: ['foo'] }),
      });
    }
  });

  await page.goto('/images/review');
  await expect(page.getByText('Image Review')).toBeVisible();
  const rating = page.locator('[data-testid="rating-1"]');
  await rating.selectOption('5');
  await expect(rating).toHaveValue('5');
  const tags = page.locator('[data-testid="tags-1"]');
  await tags.fill('foo');
  await expect(tags).toHaveValue('foo');
});
