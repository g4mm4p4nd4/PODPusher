import { test, expect } from '@playwright/test';

test('language switcher updates navigation text', async ({ page }) => {
  await page.goto('/');
  await page.getByTestId('language-switcher').selectOption('es');
  await expect(page.getByRole('link', { name: 'Inicio' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Generar' })).toBeVisible();
});
