import { test, expect } from '@playwright/test';

test('language switcher updates navigation text', async ({ page }, testInfo) => {
  await page.goto('/');
  const target = testInfo.project.name === 'es' ? 'en' : 'es';
  await page.getByTestId('language-switcher').selectOption(target);
  if (target === 'es') {
    await expect(page.getByRole('link', { name: 'Inicio' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Generar' })).toBeVisible();
  } else {
    await expect(page.getByRole('link', { name: 'Home' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Generate' })).toBeVisible();
  }
});
