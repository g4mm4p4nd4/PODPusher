import { test, expect } from '@playwright/test';

test('listing composer saves draft', async ({ page }) => {
  await page.route('**/api/listing-composer/drafts', route => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          title: 'T',
          description: 'D',
          tags: [],
          language: 'en',
          field_order: ['title', 'description', 'tags']
        })
      });
    } else {
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'not found' })
      });
    }
  });

  await page.goto('/listings');
  await page.getByLabel('Title').fill('T');
  await page.getByLabel('Description').fill('D');
  await page.getByRole('button', { name: 'Save' }).click();
  const id = await page.evaluate(() => window.localStorage.getItem('draftId'));
  expect(id).toBe('1');
});
