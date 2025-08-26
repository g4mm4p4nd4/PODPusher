import { test, expect } from '@playwright/test';

test('search page filters products', async ({ page }) => {
  await page.route('**/product-categories', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ name: 'apparel' }]),
    });
  });

  await page.route('**/api/search**', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 1,
            name: 'Product 1',
            description: 'funny dog shirt',
            image_url: '/test.png',
            rating: 4,
            tags: ['funny'],
            category: 'apparel',
          },
        ],
        total: 1,
      }),
    });
  });

  await page.goto('/search');
  await page.getByPlaceholder('Keyword').fill('dog');
  await page.getByRole('button', { name: 'Search' }).click();
  await expect(page.getByText('Product 1')).toBeVisible();
});
