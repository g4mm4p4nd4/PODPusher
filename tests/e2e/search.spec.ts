import { test, expect } from '@playwright/test';

const result = {
  total: 1,
  items: [
    {
      id: 1,
      name: 'Product 1',
      description: 'Cute cat mug',
      category: 'animals',
      image_url: '/img.png',
      rating: 5,
      tags: ['cute'],
    },
  ],
};

test('search filters results', async ({ page }) => {
  await page.route('**/api/search**', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(result) });
  });
  await page.route('**/product-categories', route => {
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ name: 'animals' }]) });
  });

  await page.goto('/search');
  await page.getByPlaceholder('Keyword').fill('cat');
  await page.getByRole('button', { name: 'Search' }).click();
  await expect(page.getByText('Cute cat mug')).toBeVisible();
});
