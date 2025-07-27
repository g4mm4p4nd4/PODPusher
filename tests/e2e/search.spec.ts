import { test, expect } from '@playwright/test';

test('search page filters results', async ({ page }) => {
  await page.route('**/api/search**', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, image_url: '/img.png', rating: 5, tags: ['cat'], idea: 'cat tee', term: 'cat', category: 'animals' },
      ]),
    });
  });
  await page.goto('/search');
  await page.getByPlaceholderText('keyword').fill('cat');
  await page.getByText('Search').click();
  await expect(page.getByTestId('result')).toHaveCount(1);
});
